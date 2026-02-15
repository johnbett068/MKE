from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import CancellationConfig
from wallets.services import WalletService
from .events import RideEventBroadcaster


class CancellationService:

    @staticmethod
    def cancel_ride(ride, cancelled_by):

        config = CancellationConfig.objects.first()

        if ride.status in ['completed', 'cancelled']:
            raise ValueError("Ride already ended.")

        # If no driver assigned → free cancellation
        if not ride.driver:
            ride.status = 'cancelled'
            ride.save()
            return {"message": "Ride cancelled successfully."}

        time_since_acceptance = timezone.now() - ride.created_at

        free_window = timedelta(
            minutes=config.free_cancellation_minutes
        )

        # 🟢 Rider Cancels
        if cancelled_by == ride.customer:

            if time_since_acceptance > free_window:

                fee = config.rider_cancellation_fee

                WalletService.deduct_funds(
                    user=ride.customer,
                    amount=Decimal(fee),
                    description="Cancellation fee"
                )

                WalletService.add_funds(
                    user=ride.driver,
                    amount=Decimal(fee),
                    description="Compensation for cancellation"
                )

                result = {
                    "message": "Ride cancelled. Fee applied.",
                    "fee": str(fee)
                }

            else:
                result = {"message": "Ride cancelled within free window."}

        # 🔴 Driver Cancels
        else:

            driver = ride.driver.driver_profile
            driver.cancellation_count += 1
            driver.save(update_fields=['cancellation_count'])

            result = {
                "message": "Driver cancelled. Penalty recorded.",
                "driver_cancellation_count": driver.cancellation_count
            }

        ride.status = 'cancelled'
        ride.save()

        RideEventBroadcaster.broadcast(
            ride.id,
            "ride_cancelled",
            result
        )

        return result

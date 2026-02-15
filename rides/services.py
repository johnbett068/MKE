from django.db import transaction
from decimal import Decimal

from pricing.services import PricingService
from commissions.services import CommissionService
from wallets.services import WalletService
from notifications.services import NotificationService
from .models import DriverAvailability
from .utils import haversine_distance
from .events import RideEventBroadcaster
from .cancellation_service import CancellationService


# Allowed ride status transitions
ALLOWED_TRANSITIONS = {
    'requested': ['accepted', 'cancelled'],
    'accepted': ['in_progress', 'cancelled'],
    'in_progress': ['completed', 'cancelled'],
    'completed': [],
    'cancelled': [],
}


# --------------------------------------------------
# Ride Service (Lifecycle + Financials + Events)
# --------------------------------------------------
class RideService:

    # -------------------------------
    # Status transition controller
    # -------------------------------
    @staticmethod
    def change_status(ride, new_status):

        if new_status not in ALLOWED_TRANSITIONS.get(ride.status, []):
            raise ValueError(
                f"Invalid transition from {ride.status} to {new_status}"
            )

        ride.status = new_status
        ride.save(update_fields=["status"])
        return ride

    # -------------------------------
    # Ride lifecycle methods
    # -------------------------------
    @staticmethod
    def accept_ride(ride, driver):

        if ride.status != 'requested':
            raise ValueError("Ride cannot be accepted.")

        ride.driver = driver
        ride.status = 'accepted'
        ride.save(update_fields=["driver", "status"])

        # Mark driver busy
        DriverAvailability.objects.filter(driver=driver).update(status='busy')

        # Broadcast event
        RideEventBroadcaster.broadcast(
            ride.id,
            "ride_accepted",
            {
                "driver_id": driver.id,
                "message": "Driver accepted your ride."
            }
        )

        return ride

    @staticmethod
    def start_ride(ride):

        if ride.status != 'accepted':
            raise ValueError("Ride cannot start.")

        ride.status = 'in_progress'
        ride.save(update_fields=["status"])

        RideEventBroadcaster.broadcast(
            ride.id,
            "ride_started",
            {
                "message": "Ride has started."
            }
        )

        return ride

    # -------------------------------
    # NEW cancellation flow
    # -------------------------------
    @staticmethod
    def cancel_ride(ride, cancelled_by):
        return CancellationService.cancel_ride(ride, cancelled_by)

    @staticmethod
    def complete_ride(
        ride,
        distance_km,
        duration_minutes,
        pickup_zone=None,
        dropoff_zone=None
    ):

        if ride.status != 'in_progress':
            raise ValueError("Ride must be in progress to complete.")

        ride.status = 'completed'
        ride.save(update_fields=["status"])

        result = RideService._handle_financials(
            ride,
            distance_km,
            duration_minutes,
            pickup_zone,
            dropoff_zone
        )

        # Release driver back to pool
        if ride.driver:
            DriverAvailability.objects.filter(driver=ride.driver).update(status='available')

        RideEventBroadcaster.broadcast(
            ride.id,
            "ride_completed",
            {
                "total_fare": str(ride.total_fare),
                "driver_payout": str(ride.driver_payout),
                "message": "Ride completed successfully."
            }
        )

        return result

    # -------------------------------
    # Financial orchestration
    # -------------------------------
    @staticmethod
    def _handle_financials(
        ride,
        distance_km,
        duration_minutes,
        pickup_zone,
        dropoff_zone
    ):

        with transaction.atomic():

            total_fare = PricingService.calculate_fare(
                city=ride.city,
                service_type="ride",
                distance_km=distance_km,
                duration_minutes=duration_minutes,
                pickup_zone=pickup_zone,
                dropoff_zone=dropoff_zone
            )

            commission_amount = CommissionService.calculate_commission(
                amount=total_fare,
                service_type="ride",
                role="driver"
            )

            driver_payout = Decimal(total_fare) - Decimal(commission_amount)

            ride.total_fare = total_fare
            ride.commission_amount = commission_amount
            ride.driver_payout = driver_payout
            ride.save(update_fields=[
                "total_fare",
                "commission_amount",
                "driver_payout"
            ])

            WalletService.deduct_funds(
                user=ride.customer,
                amount=Decimal(total_fare),
                description="Ride payment"
            )

            WalletService.add_funds(
                user=ride.driver,
                amount=Decimal(driver_payout),
                description="Ride earnings"
            )

            NotificationService.create_notification(
                recipient=ride.customer,
                notification_type='ride_update',
                title='Ride Completed',
                message=f'You were charged {total_fare}',
                reference_id=str(ride.id)
            )

            NotificationService.create_notification(
                recipient=ride.driver,
                notification_type='ride_update',
                title='Ride Earnings Credited',
                message=f'You earned {driver_payout}',
                reference_id=str(ride.id)
            )

            return {
                "total_fare": total_fare,
                "commission": commission_amount,
                "driver_payout": driver_payout
            }


# --------------------------------------------------
# Ride Matching Service (Nearest Driver)
# --------------------------------------------------
class RideMatchingService:

    @staticmethod
    @transaction.atomic
    def find_and_assign_nearest_driver(ride, search_radius_km=10):

        if ride.status != 'requested':
            raise ValueError("Ride is not in requested state.")

        if not ride.pickup_latitude or not ride.pickup_longitude:
            raise ValueError("Ride has no pickup coordinates.")

        available_drivers = DriverAvailability.objects.select_for_update().filter(
            status='available',
            driver__city=ride.city,
            current_latitude__isnull=False,
            current_longitude__isnull=False
        )

        nearest_driver = None
        shortest_distance = None

        for driver_availability in available_drivers:

            distance = haversine_distance(
                ride.pickup_latitude,
                ride.pickup_longitude,
                driver_availability.current_latitude,
                driver_availability.current_longitude
            )

            if distance <= search_radius_km:
                if shortest_distance is None or distance < shortest_distance:
                    shortest_distance = distance
                    nearest_driver = driver_availability

        if not nearest_driver:
            return None

        ride.driver = nearest_driver.driver
        ride.status = 'accepted'
        ride.save(update_fields=["driver", "status"])

        nearest_driver.status = 'busy'
        nearest_driver.save(update_fields=["status"])

        RideEventBroadcaster.broadcast(
            ride.id,
            "ride_accepted",
            {
                "driver_id": nearest_driver.driver.id,
                "message": "Driver accepted your ride."
            }
        )

        return nearest_driver.driver

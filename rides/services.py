from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from accounts.models import AccountRole
from commissions.services import CommissionService
from core.events import RealtimeEventService, driver_group, trip_group
from drivers.models import Driver
from notifications.services import NotificationService
from pricing.services import PricingService
from wallets.models import Wallet
from wallets.services import WalletService

from .models import (
    CancellationConfig,
    Ride,
    Trip,
    TripCancellation,
    TripEvent,
    TripOffer,
)
from .security import verify_start_pin
from .utils import haversine_distance


ALLOWED_TRANSITIONS = {
    "requested": {"accepted", "cancelled"},
    "accepted": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def is_approved_driver(user):
    return (
        AccountRole.objects.filter(
            account=user,
            role__name="driver",
            status="approved",
            is_active=True,
        ).exists()
        and Driver.objects.filter(user=user).exists()
    )


class RideService:
    @staticmethod
    def _event(trip, status, note=""):
        TripEvent.objects.create(trip=trip, status=status, note=note)

    @staticmethod
    def _record_event(trip_id, event_type, data):
        return RealtimeEventService.record(
            trip_group(trip_id),
            event_type,
            "trip",
            trip_id,
            data,
        )

    @classmethod
    @transaction.atomic
    def accept_trip(cls, trip_id, driver_user):
        if not is_approved_driver(driver_user):
            raise PermissionError("An approved driver role is required.")
        trip = Trip.objects.select_for_update().get(pk=trip_id)
        driver = Driver.objects.select_for_update().get(user=driver_user)
        if trip.status != "requested" or trip.driver_id is not None:
            raise ValueError("Trip is no longer available.")
        if not driver.is_online or not driver.is_available:
            raise ValueError("Driver must be online and available.")
        trip.driver = driver_user
        trip.status = "accepted"
        trip.accepted_at = timezone.now()
        trip.save(update_fields=["driver", "status", "accepted_at", "updated_at"])
        driver.is_available = False
        driver.save(update_fields=["is_available"])
        cls._event(trip, "accepted")
        cls._record_event(
            trip.id, "driver_accepted", {"driver_id": driver_user.id}
        )
        return trip

    @classmethod
    @transaction.atomic
    def start_trip(cls, trip_id, driver_user, pin):
        trip = (
            Trip.objects.select_for_update()
            .select_related("ride_details")
            .get(pk=trip_id)
        )
        if trip.driver_id != driver_user.id:
            raise PermissionError("Only the assigned driver can start this trip.")
        if trip.status != "accepted":
            raise ValueError("Only an accepted trip can start.")
        if not verify_start_pin(trip, pin):
            raise ValueError("The ride-start PIN is incorrect.")
        trip.status = "in_progress"
        trip.started_at = timezone.now()
        trip.save(update_fields=["status", "started_at", "updated_at"])
        cls._event(trip, "in_progress")
        cls._record_event(trip.id, "trip_started", {})
        return trip

    @classmethod
    @transaction.atomic
    def mark_arrived(cls, trip_id, driver_user):
        trip = Trip.objects.select_for_update().get(pk=trip_id)
        if trip.driver_id != driver_user.id:
            raise PermissionError("Only the assigned driver can mark arrival.")
        if trip.status != "accepted":
            raise ValueError("Arrival is valid only for an accepted trip.")
        if trip.arrived_at:
            return trip
        trip.arrived_at = timezone.now()
        trip.save(update_fields=["arrived_at", "updated_at"])
        cls._event(trip, "driver_arrived")
        cls._record_event(trip.id, "driver_arrived", {})
        return trip

    @classmethod
    @transaction.atomic
    def complete_trip(cls, trip_id, driver_user, distance_km, duration_minutes):
        trip = (
            Trip.objects.select_for_update()
            .select_related("origin", "driver", "customer")
            .get(pk=trip_id)
        )
        if trip.driver_id != driver_user.id:
            raise PermissionError("Only the assigned driver can complete this trip.")
        if trip.status != "in_progress":
            raise ValueError("Only an in-progress trip can be completed.")
        fare = PricingService.calculate_fare(
            city=trip.city,
            service_type=trip.trip_type,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
        )
        commission = CommissionService.calculate_commission(
            amount=fare, service_type=trip.trip_type, role="driver"
        )
        payout = Decimal(fare) - Decimal(commission)
        ride, _ = Ride.objects.get_or_create(
            trip=trip, defaults={"city": trip.city}
        )
        ride.total_fare = fare
        ride.commission_amount = commission
        ride.driver_payout = payout
        ride.save(
            update_fields=["total_fare", "commission_amount", "driver_payout"]
        )
        reference = f"trip:{trip.id}"
        driver_wallet = Wallet.objects.select_for_update().get(
            account=trip.driver, role__name="driver", is_active=True
        )
        if trip.payment_method == "wallet":
            customer_wallet = Wallet.objects.select_for_update().get(
                account=trip.customer, role__name="customer", is_active=True
            )
            WalletService.debit_wallet(
                customer_wallet, fare, trip.trip_type, reference, "Trip payment."
            )
            if payout > 0:
                WalletService.credit_wallet(
                    driver_wallet,
                    payout,
                    trip.trip_type,
                    reference,
                    "Trip earnings.",
                )
        elif commission > 0:
            WalletService.record_cash_commission(
                driver_wallet, commission, trip.trip_type, reference
            )
        trip.status = "completed"
        trip.fare = fare
        trip.distance_km = distance_km
        trip.completed_at = timezone.now()
        trip.save(
            update_fields=[
                "status",
                "fare",
                "distance_km",
                "completed_at",
                "updated_at",
            ]
        )
        Driver.objects.filter(user=trip.driver).update(is_available=True)
        cls._event(trip, "completed")
        NotificationService.create_notification(
            recipient=trip.customer,
            notification_type="ride_update",
            title="Trip completed",
            message=f"Your final fare is {fare}.",
            reference_id=str(trip.id),
        )
        cls._record_event(
            trip.id,
            "trip_completed",
            {"total_fare": str(fare), "driver_payout": str(payout)},
        )
        return trip

    @classmethod
    @transaction.atomic
    def cancel_trip(cls, trip_id, actor, reason=""):
        trip = (
            Trip.objects.select_for_update()
            .select_related("customer", "driver")
            .get(pk=trip_id)
        )
        if actor.id not in {trip.customer_id, trip.driver_id}:
            raise PermissionError("Only a trip participant can cancel it.")
        if "cancelled" not in ALLOWED_TRANSITIONS[trip.status]:
            raise ValueError("This trip can no longer be cancelled.")
        fee = Decimal("0")
        fee_status = "not_applicable"
        config = CancellationConfig.objects.order_by("-created_at").first()
        if not config:
            config = CancellationConfig()
        is_customer = actor.id == trip.customer_id
        free_until = None
        if trip.accepted_at:
            free_until = trip.accepted_at + timedelta(
                minutes=config.free_cancellation_minutes
            )
        if (
            is_customer
            and trip.driver_id
            and free_until
            and timezone.now() > free_until
        ):
            fee = config.rider_cancellation_fee
            if trip.payment_method == "wallet":
                customer_wallet = Wallet.objects.get(
                    account=trip.customer,
                    role__name="customer",
                    is_active=True,
                )
                driver_wallet = Wallet.objects.get(
                    account=trip.driver,
                    role__name="driver",
                    is_active=True,
                )
                reference = f"trip-cancellation:{trip.id}"
                WalletService.debit_wallet(
                    customer_wallet,
                    fee,
                    "ride_cancellation",
                    reference,
                    "Late cancellation fee.",
                )
                WalletService.credit_wallet(
                    driver_wallet,
                    fee,
                    "ride_cancellation",
                    reference,
                    "Cancellation compensation.",
                )
                fee_status = "paid"
            else:
                fee_status = "due"
        elif not is_customer and trip.driver_id == actor.id:
            driver = Driver.objects.select_for_update().get(user=actor)
            driver.cancellation_count += 1
            if driver.cancellation_count >= config.driver_cancellation_penalty_limit:
                driver.is_available = False
            driver.save(update_fields=["cancellation_count", "is_available"])

        trip.status = "cancelled"
        trip.cancelled_at = timezone.now()
        trip.save(update_fields=["status", "cancelled_at", "updated_at"])
        if trip.driver_id and is_customer:
            Driver.objects.filter(user_id=trip.driver_id).update(is_available=True)
        TripCancellation.objects.create(
            trip=trip,
            cancelled_by=actor,
            reason=reason,
            fee_amount=fee,
            fee_status=fee_status,
        )
        cls._event(trip, "cancelled", f"Cancelled by account {actor.id}.")
        cls._record_event(
            trip.id,
            "trip_cancelled",
            {"cancelled_by": actor.id, "fee_amount": str(fee)},
        )
        return trip


class RideMatchingService:
    @staticmethod
    def nearest_available_drivers(trip, search_radius_km=10):
        details = getattr(trip, "ride_details", None)
        if not details or details.pickup_latitude is None:
            return []
        candidates = Driver.objects.filter(
            is_online=True,
            is_available=True,
            current_latitude__isnull=False,
            current_longitude__isnull=False,
            user__roles__role__name="driver",
            user__roles__status="approved",
            user__roles__is_active=True,
        ).distinct()
        matches = []
        for driver in candidates:
            distance = haversine_distance(
                details.pickup_latitude,
                details.pickup_longitude,
                driver.current_latitude,
                driver.current_longitude,
            )
            if distance <= search_radius_km:
                matches.append((distance, driver))
        return [driver for _, driver in sorted(matches, key=lambda item: item[0])]


class DispatchService:
    OFFER_SECONDS = 30
    MAX_CANDIDATES = 5

    @classmethod
    @transaction.atomic
    def create_offers(cls, trip):
        drivers = RideMatchingService.nearest_available_drivers(trip)
        offers = []
        for driver in drivers[: cls.MAX_CANDIDATES]:
            distance = haversine_distance(
                trip.ride_details.pickup_latitude,
                trip.ride_details.pickup_longitude,
                driver.current_latitude,
                driver.current_longitude,
            )
            offer, _ = TripOffer.objects.get_or_create(
                trip=trip,
                driver=driver.user,
                defaults={
                    "distance_to_pickup_km": Decimal(str(distance)).quantize(
                        Decimal("0.01")
                    ),
                    "expires_at": timezone.now()
                    + timedelta(seconds=cls.OFFER_SECONDS),
                },
            )
            offers.append(offer)
            RealtimeEventService.record(
                driver_group(driver.user_id),
                "offer_received",
                "trip_offer",
                offer.id,
                {
                    "offer_id": offer.id,
                    "trip_id": trip.id,
                    "distance_to_pickup_km": str(
                        offer.distance_to_pickup_km
                    ),
                    "quoted_fare": str(trip.quoted_fare),
                    "expires_at": offer.expires_at.isoformat(),
                    "origin": {
                        "id": trip.origin_id,
                        "name": str(trip.origin),
                    },
                    "destination": {
                        "id": trip.destination_id,
                        "name": str(trip.destination),
                    },
                },
            )
        return offers

    @staticmethod
    @transaction.atomic
    def accept_offer(offer_id, driver_user):
        offer = (
            TripOffer.objects.select_for_update()
            .select_related("trip")
            .get(pk=offer_id, driver=driver_user)
        )
        if not offer.is_actionable:
            if offer.status == "pending":
                offer.status = "expired"
                offer.save(update_fields=["status"])
            raise ValueError("This offer is no longer available.")
        trip = Trip.objects.select_for_update().get(pk=offer.trip_id)
        driver = Driver.objects.select_for_update().get(user=driver_user)
        if trip.status != "requested" or trip.driver_id:
            offer.status = "withdrawn"
            offer.save(update_fields=["status"])
            raise ValueError("This trip was assigned to another driver.")
        if not driver.is_online or not driver.is_available:
            raise ValueError("Driver must be online and available.")
        trip.driver = driver_user
        trip.vehicle = driver_user.vehicles.filter(is_active=True).first()
        trip.status = "accepted"
        trip.accepted_at = timezone.now()
        trip.save(
            update_fields=[
                "driver", "vehicle", "status", "accepted_at", "updated_at"
            ]
        )
        driver.is_available = False
        driver.save(update_fields=["is_available"])
        offer.status = "accepted"
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at"])
        TripOffer.objects.filter(
            trip=trip,
            status="pending",
        ).exclude(pk=offer.pk).update(status="withdrawn")
        RideService._event(trip, "accepted")
        RideService._record_event(
            trip.id,
            "driver_accepted",
            {"driver_id": driver_user.id},
        )
        return trip

    @staticmethod
    def reject_offer(offer, driver_user):
        if offer.driver_id != driver_user.id:
            raise PermissionError("This offer belongs to another driver.")
        if not offer.is_actionable:
            raise ValueError("This offer is no longer available.")
        offer.status = "rejected"
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at"])
        return offer

from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import Account
from core.models import Location
from .chat_models import RideMessage  # noqa: F401


# ---------------------------------------------------
# Vehicle model
# ---------------------------------------------------
class Vehicle(models.Model):
    driver = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )
    type = models.CharField(max_length=50)  # car, bike, van etc
    make = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    capacity = models.PositiveSmallIntegerField(default=4)
    license_plate = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.license_plate}"


# ---------------------------------------------------
# Trip model (generic)
# ---------------------------------------------------
class Trip(models.Model):

    TRIP_TYPE_CHOICES = [
        ('ride', 'Ride'),
        ('delivery', 'Delivery'),
    ]

    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('wallet', 'Wallet'),
    ]

    customer = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='trips'
    )

    driver = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_trips'
    )

    vehicle = models.ForeignKey(
        Vehicle,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    trip_type = models.CharField(
        max_length=10,
        choices=TRIP_TYPE_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='requested'
    )

    origin = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='trip_origin'
    )

    destination = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='trip_destination'
    )

    fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'
    )
    quoted_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.trip_type.capitalize()} #{self.id} ({self.status})"

    @property
    def city(self):
        return self.origin.town


# ---------------------------------------------------
# Trip events
# ---------------------------------------------------
class TripEvent(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='events'
    )
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.trip.id} → {self.status}"


# ---------------------------------------------------
# Ride-specific extension (financial + operational)
# ---------------------------------------------------
class Ride(models.Model):

    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name='ride_details'
    )

    city = models.CharField(max_length=100)

    pickup_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    pickup_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    dropoff_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    dropoff_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    total_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    driver_payout = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    start_pin_hash = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ride Trip #{self.trip.id}"


# ---------------------------------------------------
# Driver availability tracking with GPS
# ---------------------------------------------------
class DriverAvailability(models.Model):

    STATUS_CHOICES = (
        ('offline', 'Offline'),
        ('available', 'Available'),
        ('busy', 'Busy'),
    )

    driver = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name='availability'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='offline'
    )

    current_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    current_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.driver.id} - {self.status}"


# ---------------------------------------------------
# Cancellation configuration
# ---------------------------------------------------
class CancellationConfig(models.Model):

    free_cancellation_minutes = models.IntegerField(default=2)

    rider_cancellation_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=100.00
    )

    driver_cancellation_penalty_limit = models.IntegerField(default=3)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Cancellation Config"


class FareQuote(models.Model):
    customer = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="fare_quotes",
    )
    origin = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="quotes_from",
    )
    destination = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="quotes_to",
    )
    service_type = models.CharField(max_length=10, choices=Trip.TRIP_TYPE_CHOICES)
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.DecimalField(max_digits=8, decimal_places=2)
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    route_source = models.CharField(max_length=30)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_usable(self):
        return self.consumed_at is None and self.expires_at > timezone.now()


class TripOffer(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
        ("withdrawn", "Withdrawn"),
    )

    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    driver = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="trip_offers",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    distance_to_pickup_km = models.DecimalField(max_digits=8, decimal_places=2)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("trip", "driver"),
                name="one_offer_per_trip_driver",
            )
        ]

    @property
    def is_actionable(self):
        return self.status == "pending" and self.expires_at > timezone.now()


class TripCancellation(models.Model):
    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name="cancellation",
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="trip_cancellations",
    )
    reason = models.CharField(max_length=255, blank=True)
    fee_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fee_status = models.CharField(
        max_length=20,
        choices=(
            ("not_applicable", "Not applicable"),
            ("due", "Due"),
            ("paid", "Paid"),
        ),
        default="not_applicable",
    )
    created_at = models.DateTimeField(auto_now_add=True)

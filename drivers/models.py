from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class DriverApplication(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_application",
    )
    national_id_number = models.CharField(max_length=30, unique=True)
    driving_license_number = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(max_length=30)
    vehicle_make = models.CharField(max_length=50)
    vehicle_model = models.CharField(max_length=50)
    vehicle_year = models.PositiveSmallIntegerField()
    vehicle_color = models.CharField(max_length=30)
    license_plate = models.CharField(max_length=20, unique=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="submitted",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_applications_reviewed",
    )
    review_comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.email} ({self.status})"


class DriverDocument(models.Model):
    DOCUMENT_TYPES = (
        ("national_id", "National ID"),
        ("driver_license", "Driving licence"),
        ("vehicle_registration", "Vehicle registration"),
        ("insurance", "Insurance"),
        ("inspection", "Vehicle inspection"),
    )
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="driver_documents",
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100, blank=True)
    file = models.ImageField(upload_to="drivers/documents/")
    expires_at = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="driver_documents_reviewed",
    )
    review_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("account", "document_type"),
                name="one_driver_document_per_type",
            )
        ]

    def __str__(self):
        return f"{self.account.email} - {self.document_type}"


class Driver(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )

    car_model = models.CharField(max_length=100)
    license_plate = models.CharField(max_length=20, unique=True)

    is_online = models.BooleanField(default=False)
    is_available = models.BooleanField(default=False)

    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)

    last_seen = models.DateTimeField(null=True, blank=True)

    # NEW: driver cancellation penalty tracking
    cancellation_count = models.IntegerField(default=0)

    def mark_online(self):
        self.is_online = True
        self.last_seen = timezone.now()
        self.save(update_fields=['is_online', 'last_seen'])

    def mark_offline(self):
        self.is_online = False
        self.is_available = False
        self.save(update_fields=['is_online', 'is_available'])

    def update_heartbeat(self):
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])

    def __str__(self):
        return f"{self.user.email} - {self.license_plate}"

    @property
    def heartbeat_is_fresh(self):
        if not self.last_seen:
            return False
        return self.last_seen >= timezone.now() - timedelta(seconds=45)

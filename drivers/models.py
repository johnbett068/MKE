from django.db import models
from django.conf import settings
from django.utils import timezone


class Driver(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )

    car_model = models.CharField(max_length=100)
    license_plate = models.CharField(max_length=20)

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

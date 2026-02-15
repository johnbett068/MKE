# pricing/models.py

from django.db import models
from django.utils import timezone


class PricingRule(models.Model):

    SERVICE_TYPES = (
        ('ride', 'Ride'),
        ('delivery', 'Delivery'),
    )

    city = models.CharField(max_length=100)

    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES
    )

    base_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    per_km_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    per_minute_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('city', 'service_type', 'active')

    def __str__(self):
        return f"{self.city} - {self.service_type}"


class Zone(models.Model):

    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    extra_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city} - {self.name}"


class SurgePricing(models.Model):

    city = models.CharField(max_length=100)

    multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Example: 1.50 for 1.5x surge"
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_active_now(self):
        now = timezone.localtime().time()
        return self.start_time <= now <= self.end_time

    def __str__(self):
        return f"{self.city} - {self.multiplier}x Surge"

# commissions/models.py

from django.db import models
from accounts.models import Role


class CommissionRule(models.Model):

    SERVICE_TYPES = (
        ('ride', 'Ride'),
        ('delivery', 'Delivery'),
        ('shop', 'Shop Order'),
        ('housing', 'Housing Booking'),
        ('job', 'Job Posting'),
        ('marketplace', 'Marketplace'),
    )

    service_type = models.CharField(
        max_length=50,
        choices=SERVICE_TYPES
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage commission (e.g., 10.00 for 10%)"
    )

    flat_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    effective_from = models.DateField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_from']

    def __str__(self):
        return f"{self.service_type} - {self.role.name} ({self.percentage}%)"

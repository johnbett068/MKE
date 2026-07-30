# commissions/models.py

from django.db import models
from django.db.models import Q
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
        constraints = [
            models.CheckConstraint(
                condition=Q(percentage__gte=0, percentage__lte=100),
                name="commission_percentage_between_0_and_100",
            ),
            models.CheckConstraint(
                condition=Q(flat_fee__gte=0),
                name="commission_flat_fee_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.service_type} - {self.role.name} ({self.percentage}%)"

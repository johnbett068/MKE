from django.db import models
from accounts.models import Account


class Verification(models.Model):

    VERIFICATION_TYPES = (
        ('phone', 'Phone'),
        ('national_id', 'National ID'),
        ('vehicle', 'Vehicle'),
        ('business', 'Business'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='verifications'
    )

    verification_type = models.CharField(
        max_length=20,
        choices=VERIFICATION_TYPES
    )

    document_number = models.CharField(
        max_length=100,
        blank=True
    )

    document_image = models.ImageField(
        upload_to='verification/',
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verifications_reviewed'
    )

    admin_comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('account', 'verification_type')

    def __str__(self):
        return f"{self.account} - {self.verification_type} ({self.status})"

# notifications/models.py

from django.db import models
from accounts.models import Account


class Notification(models.Model):

    NOTIFICATION_TYPES = (
        ('ride_update', 'Ride Update'),
        ('wallet', 'Wallet Alert'),
        ('verification', 'Verification Update'),
        ('rating', 'Rating Received'),
        ('admin', 'Admin Message'),
        ('system', 'System Alert'),
    )

    recipient = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES
    )

    title = models.CharField(max_length=255)
    message = models.TextField()

    reference_id = models.CharField(
        max_length=100,
        blank=True
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.email} - {self.notification_type}"

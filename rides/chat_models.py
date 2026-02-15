from django.db import models
from django.conf import settings


class RideMessage(models.Model):

    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('system', 'System'),
    )

    ride = models.ForeignKey(
        'rides.Ride',  # string reference avoids circular import
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    message = models.TextField()

    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='text'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Ride {self.ride.id} - {self.sender}"

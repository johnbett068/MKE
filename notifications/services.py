# notifications/services.py

from django.db import transaction
from .models import Notification


class NotificationService:

    @staticmethod
    @transaction.atomic
    def create_notification(
        recipient,
        notification_type,
        title,
        message,
        reference_id=""
    ):
        return Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_id=reference_id
        )

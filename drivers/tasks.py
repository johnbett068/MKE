# drivers/tasks.py

from django.utils import timezone
from datetime import timedelta
from .models import Driver

HEARTBEAT_TIMEOUT_SECONDS = 45

def mark_inactive_drivers_offline():
    """
    Mark drivers offline if they haven't sent heartbeat recently.
    """
    threshold = timezone.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)
    inactive_drivers = Driver.objects.filter(
        is_online=True,
        last_seen__lt=threshold
    )

    count = inactive_drivers.count()
    for driver in inactive_drivers:
        driver.mark_offline()
    return count

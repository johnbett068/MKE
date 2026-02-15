# drivers/tasks.py

from django.utils import timezone
from datetime import timedelta
from .models import Driver

HEARTBEAT_TIMEOUT_SECONDS = 30  # If no heartbeat for 30s, mark offline

def mark_inactive_drivers_offline():
    """
    Mark drivers offline if they haven't sent heartbeat recently.
    """
    threshold = timezone.now() - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)
    inactive_drivers = Driver.objects.filter(
        is_online=True,
        last_seen__lt=threshold
    )

    for driver in inactive_drivers:
        driver.mark_offline()

    print(f"{inactive_drivers.count()} drivers marked offline.")

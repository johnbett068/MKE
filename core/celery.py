# core/celery.py

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'making_life_easier.settings')

# Initialize Celery
app = Celery('making_life_easier')

# Read config from Django settings, using CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks from all installed apps
app.autodiscover_tasks()

# -------------------------------
# Beat schedule (periodic tasks)
# -------------------------------
app.conf.beat_schedule = {
    "check-driver-heartbeats": {
        "task": "drivers.tasks.mark_inactive_drivers_offline",
        "schedule": 10.0,  # Run every 10 seconds
    },
}

# Optional: use UTC
app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

from django.core.management.base import BaseCommand

from drivers.tasks import mark_inactive_drivers_offline


class Command(BaseCommand):
    help = "Mark online drivers offline when their heartbeat has expired."

    def handle(self, *args, **options):
        count = mark_inactive_drivers_offline()
        self.stdout.write(
            self.style.SUCCESS(f"Marked {count} inactive driver(s) offline.")
        )

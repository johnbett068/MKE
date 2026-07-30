from django.core.management.base import BaseCommand
from django.utils import timezone

from rides.models import TripOffer


class Command(BaseCommand):
    help = "Expire pending dispatch offers whose response window has elapsed."

    def handle(self, *args, **options):
        count = TripOffer.objects.filter(
            status="pending",
            expires_at__lte=timezone.now(),
        ).update(status="expired")
        self.stdout.write(self.style.SUCCESS(f"Expired {count} trip offer(s)."))

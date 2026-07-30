import time

from django.core.management.base import BaseCommand

from core.events import RealtimeEventService


class Command(BaseCommand):
    help = "Publish pending durable real-time events from the transactional outbox."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--watch", action="store_true")
        parser.add_argument("--interval", type=float, default=1.0)

    def handle(self, *args, **options):
        if not options["watch"]:
            count = RealtimeEventService.publish_pending(limit=options["limit"])
            self.stdout.write(self.style.SUCCESS(f"Published {count} event(s)."))
            return
        interval = max(0.1, options["interval"])
        self.stdout.write("Watching the transactional outbox.")
        while True:
            count = RealtimeEventService.publish_pending(limit=options["limit"])
            if count:
                self.stdout.write(f"Published {count} event(s).")
                continue
            time.sleep(interval)

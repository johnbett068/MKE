import time

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run recurring, idempotent mobility maintenance commands."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=15)
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        interval = max(1, options["interval"])
        self.stdout.write("Starting mobility maintenance loop.")
        while True:
            call_command("expire_driver_heartbeats")
            call_command("expire_trip_offers")
            if options["once"]:
                return
            time.sleep(interval)

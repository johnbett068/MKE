from unittest.mock import patch

from django.test import TestCase

from .events import RealtimeEventService, trip_group
from .models import EventOutbox


class EventOutboxTests(TestCase):
    @patch("core.events.RealtimeEventService.send")
    def test_durable_event_uses_versioned_envelope_and_publishes_once(self, send):
        with self.captureOnCommitCallbacks(execute=True):
            event = RealtimeEventService.record(
                trip_group(42),
                "trip_started",
                "trip",
                42,
                {"driver_id": 7},
            )
        event.refresh_from_db()
        self.assertIsNotNone(event.published_at)
        envelope = send.call_args.args[1]
        self.assertEqual(envelope["schema_version"], "1.0")
        self.assertEqual(envelope["type"], "trip_started")
        self.assertEqual(envelope["aggregate"], {"type": "trip", "id": "42"})
        self.assertEqual(EventOutbox.objects.count(), 1)
        self.assertFalse(RealtimeEventService.publish(event.pk))
        self.assertEqual(send.call_count, 1)

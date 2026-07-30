import logging
import uuid

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone

from .models import EventOutbox


logger = logging.getLogger(__name__)


def trip_group(trip_id):
    return f"v1.trip.{trip_id}"


def driver_group(account_id):
    return f"v1.driver.{account_id}"


def event_envelope(event_type, aggregate_type, aggregate_id, data):
    return {
        "schema_version": "1.0",
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "occurred_at": timezone.now().isoformat(),
        "aggregate": {
            "type": aggregate_type,
            "id": str(aggregate_id),
        },
        "data": data,
    }


class RealtimeEventService:
    @staticmethod
    def send(group, envelope):
        async_to_sync(get_channel_layer().group_send)(
            group,
            {"type": "realtime.event", "envelope": envelope},
        )

    @classmethod
    def emit_ephemeral(
        cls, group, event_type, aggregate_type, aggregate_id, data
    ):
        envelope = event_envelope(
            event_type, aggregate_type, aggregate_id, data
        )
        cls.send(group, envelope)
        return envelope

    @classmethod
    def record(
        cls, group, event_type, aggregate_type, aggregate_id, data
    ):
        event = EventOutbox.objects.create(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            audience_group=group,
            payload=data,
        )
        transaction.on_commit(lambda: cls.publish(event.pk))
        return event

    @classmethod
    def publish(cls, event_pk):
        event = EventOutbox.objects.filter(pk=event_pk).first()
        if not event or event.published_at:
            return False
        try:
            cls.send(event.audience_group, event.envelope())
        except Exception as exc:
            EventOutbox.objects.filter(pk=event.pk).update(
                attempts=event.attempts + 1,
                last_error=str(exc)[:2000],
            )
            logger.exception("Failed to publish outbox event %s", event.event_id)
            return False
        EventOutbox.objects.filter(pk=event.pk).update(
            published_at=timezone.now(),
            attempts=event.attempts + 1,
            last_error="",
        )
        return True

    @classmethod
    def publish_pending(cls, limit=100):
        event_ids = list(
            EventOutbox.objects.filter(published_at__isnull=True)
            .order_by("occurred_at")
            .values_list("pk", flat=True)[:limit]
        )
        return sum(cls.publish(event_id) for event_id in event_ids)

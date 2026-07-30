import uuid

from django.db import models

class Location(models.Model):
    country = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    town = models.CharField(max_length=100)
    zone = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"{self.town}, {self.county}, {self.country}"


class EventOutbox(models.Model):
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    schema_version = models.CharField(max_length=10, default="1.0")
    event_type = models.CharField(max_length=100)
    aggregate_type = models.CharField(max_length=50)
    aggregate_id = models.CharField(max_length=100)
    audience_group = models.CharField(max_length=150)
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ("occurred_at",)
        indexes = [
            models.Index(fields=("published_at", "occurred_at")),
        ]

    def envelope(self):
        return {
            "schema_version": self.schema_version,
            "event_id": str(self.event_id),
            "type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate": {
                "type": self.aggregate_type,
                "id": self.aggregate_id,
            },
            "data": self.payload,
        }

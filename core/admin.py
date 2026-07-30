from django.contrib import admin
from .models import EventOutbox, Location

admin.site.register(Location)


@admin.register(EventOutbox)
class EventOutboxAdmin(admin.ModelAdmin):
    list_display = (
        "event_id", "event_type", "aggregate_type", "aggregate_id",
        "occurred_at", "published_at", "attempts",
    )
    list_filter = ("event_type", "published_at")
    search_fields = ("event_id", "aggregate_id", "audience_group")
    readonly_fields = (
        "event_id", "schema_version", "event_type", "aggregate_type",
        "aggregate_id", "audience_group", "payload", "occurred_at",
        "published_at", "attempts", "last_error",
    )

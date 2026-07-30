from django.contrib import admin

from .models import PaymentIntent, PaymentWebhookEvent


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = (
        "public_id", "account", "purpose", "amount", "status",
        "provider_reference", "created_at",
    )
    list_filter = ("purpose", "status", "provider")
    search_fields = (
        "public_id", "account__email", "phone_number", "provider_reference"
    )
    readonly_fields = (
        "public_id", "account", "wallet", "purpose", "amount", "currency",
        "phone_number", "provider", "provider_reference", "idempotency_key",
        "status", "failure_reason", "metadata", "created_at", "updated_at",
        "completed_at",
    )


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "received_at", "processed_at")
    search_fields = ("event_id",)
    readonly_fields = (
        "provider", "event_id", "payload", "processed_at",
        "processing_error", "received_at",
    )

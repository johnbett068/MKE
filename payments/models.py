import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class PaymentIntent(models.Model):
    PURPOSE_CHOICES = (
        ("wallet_topup", "Wallet top-up"),
        ("cash_debt", "Cash commission debt settlement"),
    )
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    )

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payment_intents",
    )
    wallet = models.ForeignKey(
        "wallets.Wallet",
        on_delete=models.PROTECT,
        related_name="payment_intents",
    )
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="KES")
    phone_number = models.CharField(max_length=20)
    provider = models.CharField(max_length=30, default="mpesa")
    provider_reference = models.CharField(max_length=100, blank=True)
    idempotency_key = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    failure_reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("account", "idempotency_key"),
                name="payment_intent_account_idempotency_unique",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="payment_intent_amount_positive",
            ),
            models.UniqueConstraint(
                fields=("provider", "provider_reference"),
                condition=~Q(provider_reference=""),
                name="payment_provider_reference_unique",
            ),
        ]


class PaymentWebhookEvent(models.Model):
    provider = models.CharField(max_length=30)
    event_id = models.CharField(max_length=150)
    payload = models.JSONField()
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "event_id"),
                name="payment_webhook_provider_event_unique",
            )
        ]

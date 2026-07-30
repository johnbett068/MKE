from rest_framework import serializers

from .models import PaymentIntent


class InitiateStkPushSerializer(serializers.Serializer):
    wallet_id = serializers.IntegerField()
    purpose = serializers.ChoiceField(
        choices=["wallet_topup", "cash_debt"]
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    phone_number = serializers.RegexField(r"^\+?254\d{9}$")


class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntent
        fields = [
            "public_id", "wallet", "purpose", "amount", "currency",
            "phone_number", "provider", "provider_reference", "status",
            "failure_reason", "created_at", "updated_at", "completed_at",
        ]
        read_only_fields = fields

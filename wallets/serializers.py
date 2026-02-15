from rest_framework import serializers
from .models import Wallet, Transaction


class WalletSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField()

    class Meta:
        model = Wallet
        fields = [
            'id',
            'role',
            'available_balance',
            'pending_balance',
            'debt_balance',
            'is_active',
        ]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_type',
            'amount',
            'service',
            'reference_id',
            'description',
            'created_at',
        ]

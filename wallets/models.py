from django.db import models
from django.db.models import Q
from accounts.models import Account, Role


class Wallet(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='wallets'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE
    )

    available_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    pending_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    debt_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('account', 'role')
        constraints = [
            models.CheckConstraint(
                condition=Q(available_balance__gte=0),
                name="wallet_available_balance_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(pending_balance__gte=0),
                name="wallet_pending_balance_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(debt_balance__gte=0),
                name="wallet_debt_balance_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.account} - {self.role.name} Wallet"


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    service = models.CharField(
        max_length=50
    )
    reference_id = models.CharField(
        max_length=100
    )

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="wallet_transaction_amount_positive",
            ),
            models.UniqueConstraint(
                fields=[
                    "wallet",
                    "transaction_type",
                    "service",
                    "reference_id",
                ],
                name="wallet_transaction_operation_unique",
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type.upper()} {self.amount}"

from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import Transaction, Wallet


class WalletService:
    @staticmethod
    def _amount(value):
        try:
            amount = Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("Amount must be a valid decimal.") from exc
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        return amount

    @staticmethod
    def _locked(wallet):
        return Wallet.objects.select_for_update().get(pk=wallet.pk)

    @classmethod
    @transaction.atomic
    def credit_wallet(cls, wallet, amount, service, reference_id, description=""):
        amount = cls._amount(amount)
        locked = cls._locked(wallet)
        existing = Transaction.objects.filter(
            wallet=locked,
            transaction_type="credit",
            service=service,
            reference_id=reference_id,
        ).first()
        if existing:
            return existing
        locked.available_balance += amount
        locked.save(update_fields=["available_balance"])
        return Transaction.objects.create(
            wallet=locked,
            transaction_type="credit",
            amount=amount,
            service=service,
            reference_id=reference_id,
            description=description,
        )

    @classmethod
    @transaction.atomic
    def debit_wallet(cls, wallet, amount, service, reference_id, description=""):
        amount = cls._amount(amount)
        locked = cls._locked(wallet)
        existing = Transaction.objects.filter(
            wallet=locked,
            transaction_type="debit",
            service=service,
            reference_id=reference_id,
        ).first()
        if existing:
            return existing
        if locked.available_balance < amount:
            raise ValueError("Insufficient wallet balance.")
        locked.available_balance -= amount
        locked.save(update_fields=["available_balance"])
        return Transaction.objects.create(
            wallet=locked,
            transaction_type="debit",
            amount=amount,
            service=service,
            reference_id=reference_id,
            description=description,
        )

    @classmethod
    @transaction.atomic
    def record_cash_commission(
        cls, wallet, commission_amount, service, reference_id
    ):
        amount = cls._amount(commission_amount)
        locked = cls._locked(wallet)
        existing = Transaction.objects.filter(
            wallet=locked,
            transaction_type="debit",
            service=service,
            reference_id=reference_id,
        ).first()
        if existing:
            return existing
        locked.debt_balance += amount
        locked.save(update_fields=["debt_balance"])
        return Transaction.objects.create(
            wallet=locked,
            transaction_type="debit",
            amount=amount,
            service=service,
            reference_id=reference_id,
            description="Cash commission recorded as provider debt.",
        )

    @classmethod
    @transaction.atomic
    def settle_cash_debt(cls, wallet, amount, service, reference_id):
        amount = cls._amount(amount)
        locked = cls._locked(wallet)
        existing = Transaction.objects.filter(
            wallet=locked,
            transaction_type="credit",
            service=service,
            reference_id=reference_id,
        ).first()
        if existing:
            return existing
        if amount > locked.debt_balance:
            raise ValueError("Settlement exceeds wallet cash debt.")
        locked.debt_balance -= amount
        locked.save(update_fields=["debt_balance"])
        return Transaction.objects.create(
            wallet=locked,
            transaction_type="credit",
            amount=amount,
            service=service,
            reference_id=reference_id,
            description="Cash commission debt settled.",
        )

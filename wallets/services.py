from decimal import Decimal
from django.db import transaction as db_transaction
from .models import Wallet, Transaction


class WalletService:

    @staticmethod
    @db_transaction.atomic
    def credit_wallet(wallet, amount, service, reference_id, description=""):
        amount = Decimal(amount)

        wallet.available_balance += amount
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            transaction_type='credit',
            amount=amount,
            service=service,
            reference_id=reference_id,
            description=description
        )

    @staticmethod
    @db_transaction.atomic
    def debit_wallet(wallet, amount, service, reference_id, description=""):
        amount = Decimal(amount)

        if wallet.available_balance < amount:
            raise ValueError("Insufficient wallet balance")

        wallet.available_balance -= amount
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            transaction_type='debit',
            amount=amount,
            service=service,
            reference_id=reference_id,
            description=description
        )

    @staticmethod
    @db_transaction.atomic
    def record_cash_commission(wallet, commission_amount, service, reference_id):
        commission_amount = Decimal(commission_amount)

        wallet.debt_balance += commission_amount
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            transaction_type='debit',
            amount=commission_amount,
            service=service,
            reference_id=reference_id,
            description="Cash commission recorded as debt"
        )

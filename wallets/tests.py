from decimal import Decimal

from django.test import TestCase

from accounts.models import Account, Role
from .models import Transaction, Wallet
from .services import WalletService


class WalletServiceTests(TestCase):
    def setUp(self):
        account = Account.objects.create_user("wallet@example.com", "Pass12345!")
        role = Role.objects.get(name="customer")
        self.wallet = Wallet.objects.create(account=account, role=role)

    def test_credit_is_idempotent(self):
        WalletService.credit_wallet(
            self.wallet, "100.00", "test", "same-reference"
        )
        WalletService.credit_wallet(
            self.wallet, "100.00", "test", "same-reference"
        )

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, Decimal("100.00"))
        self.assertEqual(Transaction.objects.count(), 1)

    def test_rejects_non_positive_amount(self):
        with self.assertRaisesMessage(ValueError, "greater than zero"):
            WalletService.credit_wallet(self.wallet, "0", "test", "zero")

    def test_debit_requires_funds(self):
        with self.assertRaisesMessage(ValueError, "Insufficient"):
            WalletService.debit_wallet(
                self.wallet, "1.00", "test", "insufficient"
            )

from decimal import Decimal

from django.test import TestCase

from accounts.models import Account, Role
from wallets.models import Wallet
from wallets.services import WalletService
from .models import PaymentIntent, PaymentWebhookEvent
from .services import PaymentService


class FakeMpesaGateway:
    def initiate_stk_push(self, intent):
        return {
            "CheckoutRequestID": f"checkout-{intent.public_id}",
            "MerchantRequestID": f"merchant-{intent.public_id}",
        }


def callback(checkout_id, result_code=0, amount="500.00"):
    return {
        "Body": {
            "stkCallback": {
                "CheckoutRequestID": checkout_id,
                "ResultCode": result_code,
                "ResultDesc": "Success" if result_code == 0 else "Failed",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": float(amount)},
                        {"Name": "MpesaReceiptNumber", "Value": "TEST123"},
                    ]
                },
            }
        }
    }


class PaymentServiceTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            "payer@example.com",
            "StrongPass123!",
            phone_number="+254700000040",
        )
        role = Role.objects.get(name="driver")
        self.wallet = Wallet.objects.create(account=self.account, role=role)

    def test_stk_intent_is_idempotent_and_callback_credits_wallet_once(self):
        first = PaymentService.create_stk_intent(
            account=self.account,
            wallet=self.wallet,
            purpose="wallet_topup",
            amount="500.00",
            phone_number=self.account.phone_number,
            idempotency_key="topup-001",
            gateway=FakeMpesaGateway(),
        )
        second = PaymentService.create_stk_intent(
            account=self.account,
            wallet=self.wallet,
            purpose="wallet_topup",
            amount="500.00",
            phone_number=self.account.phone_number,
            idempotency_key="topup-001",
            gateway=FakeMpesaGateway(),
        )
        self.assertEqual(first.pk, second.pk)
        payload = callback(first.provider_reference)
        PaymentService.process_mpesa_callback(payload)
        PaymentService.process_mpesa_callback(payload)
        self.wallet.refresh_from_db()
        first.refresh_from_db()
        self.assertEqual(self.wallet.available_balance, Decimal("500.00"))
        self.assertEqual(first.status, "completed")
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)

    def test_successful_debt_payment_reduces_cash_commission_debt(self):
        WalletService.record_cash_commission(
            self.wallet,
            "100.00",
            "ride",
            "trip:10",
        )
        self.wallet.refresh_from_db()
        intent = PaymentService.create_stk_intent(
            account=self.account,
            wallet=self.wallet,
            purpose="cash_debt",
            amount="60.00",
            phone_number=self.account.phone_number,
            idempotency_key="debt-001",
            gateway=FakeMpesaGateway(),
        )
        PaymentService.process_mpesa_callback(
            callback(intent.provider_reference, amount="60.00")
        )
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.debt_balance, Decimal("40.00"))
        self.assertEqual(PaymentIntent.objects.get(pk=intent.pk).status, "completed")

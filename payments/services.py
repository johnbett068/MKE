from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from wallets.models import Wallet
from wallets.services import WalletService
from .gateways import MpesaGateway
from .models import PaymentIntent, PaymentWebhookEvent


class PaymentService:
    @staticmethod
    def create_stk_intent(
        *,
        account,
        wallet,
        purpose,
        amount,
        phone_number,
        idempotency_key,
        gateway=None,
    ):
        if wallet.account_id != account.id:
            raise PermissionError("The wallet belongs to another account.")
        amount = Decimal(str(amount)).quantize(Decimal("0.01"))
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if amount != amount.to_integral_value():
            raise ValueError("M-Pesa amount must be a whole number of KES.")
        if purpose == "cash_debt" and amount > wallet.debt_balance:
            raise ValueError("Amount exceeds the wallet cash debt.")
        with transaction.atomic():
            intent, created = PaymentIntent.objects.select_for_update().get_or_create(
                account=account,
                idempotency_key=idempotency_key,
                defaults={
                    "wallet": wallet,
                    "purpose": purpose,
                    "amount": amount,
                    "phone_number": phone_number,
                    "status": "pending",
                },
            )
            if not created:
                if (
                    intent.wallet_id != wallet.id
                    or intent.purpose != purpose
                    or intent.amount != amount
                ):
                    raise ValueError(
                        "Idempotency key was already used for another request."
                    )
                if intent.status != "pending" or intent.provider_reference:
                    return intent
        gateway = gateway or MpesaGateway()
        response = gateway.initiate_stk_push(intent)
        intent.provider_reference = response.get("CheckoutRequestID", "")
        intent.status = "processing"
        intent.metadata = {"merchant_request_id": response.get("MerchantRequestID")}
        intent.save(
            update_fields=[
                "provider_reference", "status", "metadata", "updated_at"
            ]
        )
        return intent

    @staticmethod
    @transaction.atomic
    def process_mpesa_callback(payload):
        callback = payload["Body"]["stkCallback"]
        event_id = (
            f'{callback.get("CheckoutRequestID", "unknown")}:'
            f'{callback.get("ResultCode", "unknown")}'
        )
        event, created = PaymentWebhookEvent.objects.get_or_create(
            provider="mpesa",
            event_id=event_id,
            defaults={"payload": payload},
        )
        if not created and event.processed_at:
            return event
        intent = PaymentIntent.objects.select_for_update().get(
            provider_reference=callback["CheckoutRequestID"]
        )
        if intent.status == "completed":
            event.processed_at = timezone.now()
            event.save(update_fields=["processed_at"])
            return event
        if int(callback["ResultCode"]) != 0:
            intent.status = "failed"
            intent.failure_reason = callback.get("ResultDesc", "M-Pesa failed.")
            intent.save(
                update_fields=["status", "failure_reason", "updated_at"]
            )
        else:
            items = {
                item["Name"]: item.get("Value")
                for item in callback.get("CallbackMetadata", {}).get("Item", [])
            }
            received_amount = Decimal(str(items.get("Amount", "0"))).quantize(
                Decimal("0.01")
            )
            if received_amount != intent.amount:
                raise ValueError("M-Pesa callback amount does not match intent.")
            wallet = Wallet.objects.select_for_update().get(pk=intent.wallet_id)
            reference = f"payment:{intent.public_id}"
            if intent.purpose == "wallet_topup":
                WalletService.credit_wallet(
                    wallet,
                    intent.amount,
                    "payment",
                    reference,
                    "M-Pesa wallet top-up.",
                )
            else:
                WalletService.settle_cash_debt(
                    wallet,
                    intent.amount,
                    "payment",
                    reference,
                )
            intent.status = "completed"
            intent.completed_at = timezone.now()
            intent.save(
                update_fields=["status", "completed_at", "updated_at"]
            )
        event.processed_at = timezone.now()
        event.save(update_fields=["processed_at"])
        return event

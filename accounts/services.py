import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from notifications.sms import SMSService

from .models import Account, OneTimeCode


class IdentityService:
    CODE_TTL_MINUTES = 10
    MAX_REQUESTS_PER_HOUR = 5

    @staticmethod
    def _hash(account_id, purpose, code):
        payload = f"{account_id}:{purpose}:{code}".encode()
        return hmac.new(
            settings.SECRET_KEY.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

    @classmethod
    @transaction.atomic
    def issue_code(cls, account, purpose):
        since = timezone.now() - timedelta(hours=1)
        count = OneTimeCode.objects.filter(
            account=account,
            purpose=purpose,
            created_at__gte=since,
        ).count()
        if count >= cls.MAX_REQUESTS_PER_HOUR:
            raise ValueError("Too many code requests. Try again later.")
        OneTimeCode.objects.filter(
            account=account,
            purpose=purpose,
            consumed_at__isnull=True,
        ).update(consumed_at=timezone.now())
        code = f"{secrets.randbelow(1_000_000):06d}"
        OneTimeCode.objects.create(
            account=account,
            purpose=purpose,
            code_hash=cls._hash(account.id, purpose, code),
            expires_at=timezone.now() + timedelta(minutes=cls.CODE_TTL_MINUTES),
        )
        SMSService.send_code(account.phone_number, code, purpose)

    @classmethod
    @transaction.atomic
    def consume_code(cls, account, purpose, code):
        record = (
            OneTimeCode.objects.select_for_update()
            .filter(
                account=account,
                purpose=purpose,
                consumed_at__isnull=True,
            )
            .order_by("-created_at")
            .first()
        )
        if not record or not record.is_usable or record.attempts >= 5:
            raise ValueError("The code is invalid or expired.")
        expected = cls._hash(account.id, purpose, code)
        if not secrets.compare_digest(record.code_hash, expected):
            record.attempts += 1
            record.save(update_fields=["attempts"])
            raise ValueError("The code is invalid or expired.")
        record.consumed_at = timezone.now()
        record.save(update_fields=["consumed_at"])
        return record

    @classmethod
    def verify_phone(cls, account, code):
        cls.consume_code(account, "phone_verification", code)
        profile = account.profile
        profile.verification_level = max(profile.verification_level, 1)
        profile.save(update_fields=["verification_level"])

    @classmethod
    def reset_password(cls, account, code, new_password):
        validate_password(new_password, account)
        cls.consume_code(account, "password_reset", code)
        account.set_password(new_password)
        account.save(update_fields=["password"])

    @staticmethod
    def find_account(identifier):
        return Account.objects.filter(
            Q(email__iexact=identifier) | Q(phone_number=identifier)
        ).first()

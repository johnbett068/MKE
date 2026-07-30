from django.utils import timezone
from django.db import transaction
from .models import Verification


class VerificationService:
    LEVEL_BY_TYPE = {
        "phone": 1,
        "national_id": 2,
        "vehicle": 3,
        "business": 3,
    }

    @staticmethod
    @transaction.atomic
    def submit_verification(account, data):
        return Verification.objects.create(
            account=account,
            verification_type=data['verification_type'],
            document_number=data.get('document_number', ''),
            document_image=data.get('document_image')
        )

    @staticmethod
    @transaction.atomic
    def review_verification(
        verification,
        admin_user,
        status,
        comment=""
    ):
        valid_statuses = {"approved", "rejected"}
        if status not in valid_statuses:
            raise ValueError("Status must be approved or rejected.")
        verification.status = status
        verification.reviewed_by = admin_user
        verification.reviewed_at = timezone.now()
        verification.admin_comment = comment
        verification.save()
        if status == "approved":
            profile = verification.account.profile
            level = VerificationService.LEVEL_BY_TYPE[verification.verification_type]
            if profile.verification_level < level:
                profile.verification_level = level
                profile.save(update_fields=["verification_level"])
        return verification

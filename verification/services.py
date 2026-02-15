from django.utils import timezone
from django.db import transaction
from .models import Verification


class VerificationService:

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
        verification.status = status
        verification.reviewed_by = admin_user
        verification.reviewed_at = timezone.now()
        verification.admin_comment = comment
        verification.save()
        return verification

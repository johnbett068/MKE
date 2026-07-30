from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import Verification
from .serializers import (
    VerificationSerializer,
    CreateVerificationSerializer
)
from .services import VerificationService


class SubmitVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification = VerificationService.submit_verification(
            account=request.user,
            data=serializer.validated_data
        )

        return Response(
            VerificationSerializer(verification).data,
            status=status.HTTP_201_CREATED
        )


class MyVerificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        verifications = Verification.objects.filter(account=request.user)
        serializer = VerificationSerializer(verifications, many=True)
        return Response(serializer.data)


class AdminReviewVerificationView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, verification_id):
        verification = get_object_or_404(Verification, id=verification_id)

        status_value = request.data.get('status')
        comment = request.data.get('comment', '')

        try:
            verification = VerificationService.review_verification(
                verification=verification,
                admin_user=request.user,
                status=status_value,
                comment=comment
            )
        except ValueError as exc:
            raise ValidationError({"status": str(exc)}) from exc

        return Response(
            VerificationSerializer(verification).data
        )

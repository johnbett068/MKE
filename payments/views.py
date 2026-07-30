import hashlib
import json

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from wallets.models import Wallet
from .gateways import PaymentProviderError
from .models import PaymentIntent, PaymentWebhookEvent
from .serializers import InitiateStkPushSerializer, PaymentIntentSerializer
from .services import PaymentService


class ProviderUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Payment provider is temporarily unavailable."


def validate_callback_token(request):
    expected = settings.MPESA_CALLBACK_TOKEN
    if expected and request.headers.get("X-MKE-Callback-Token") != expected:
        raise PermissionDenied("Invalid callback token.")


class InitiateStkPushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key", "").strip()
        if not idempotency_key:
            raise ValidationError(
                {"Idempotency-Key": "This header is required."}
            )
        serializer = InitiateStkPushSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet = get_object_or_404(
            Wallet,
            pk=serializer.validated_data["wallet_id"],
            account=request.user,
            is_active=True,
        )
        try:
            intent = PaymentService.create_stk_intent(
                account=request.user,
                wallet=wallet,
                purpose=serializer.validated_data["purpose"],
                amount=serializer.validated_data["amount"],
                phone_number=serializer.validated_data["phone_number"],
                idempotency_key=idempotency_key,
            )
        except PaymentProviderError as exc:
            raise ProviderUnavailable(str(exc)) from exc
        except (PermissionError, ValueError) as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(PaymentIntentSerializer(intent).data, status=202)


class PaymentIntentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        intent = get_object_or_404(
            PaymentIntent,
            public_id=public_id,
            account=request.user,
        )
        return Response(PaymentIntentSerializer(intent).data)


class MpesaStkCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        validate_callback_token(request)
        try:
            PaymentService.process_mpesa_callback(request.data)
        except (KeyError, PaymentIntent.DoesNotExist, ValueError) as exc:
            raise ValidationError({"detail": "Invalid callback payload."}) from exc
        return Response({"ResultCode": 0, "ResultDesc": "Accepted"})


class MpesaGenericHookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    hook_name = "generic"

    def post(self, request):
        validate_callback_token(request)
        canonical = json.dumps(
            request.data,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        PaymentWebhookEvent.objects.get_or_create(
            provider="mpesa",
            event_id=f"{self.hook_name}:{digest}",
            defaults={"payload": request.data},
        )
        return Response({"ResultCode": 0, "ResultDesc": "Accepted"})


class MpesaC2BValidationView(MpesaGenericHookView):
    hook_name = "c2b_validation"


class MpesaC2BConfirmationView(MpesaGenericHookView):
    hook_name = "c2b_confirmation"


class MpesaB2CResultView(MpesaGenericHookView):
    hook_name = "b2c_result"

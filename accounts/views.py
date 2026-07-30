from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Account
from .serializers import (
    AccountSerializer,
    CodeRequestSerializer,
    CodeVerifySerializer,
    PasswordResetConfirmSerializer,
    PhoneLoginConfirmSerializer,
    RegisterSerializer,
)
from .services import IdentityService


class RegisterView(generics.CreateAPIView):
    queryset = Account.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RequestPhoneCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.profile.verification_level >= 1:
            return Response({"detail": "Phone number is already verified."})
        try:
            IdentityService.issue_code(request.user, "phone_verification")
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response({"detail": "Verification code sent."})


class VerifyPhoneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CodeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            IdentityService.verify_phone(
                request.user,
                serializer.validated_data["code"],
            )
        except ValueError as exc:
            raise ValidationError({"code": str(exc)}) from exc
        return Response({"detail": "Phone number verified."})


class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = IdentityService.find_account(
            serializer.validated_data["identifier"]
        )
        if account and account.phone_number:
            try:
                IdentityService.issue_code(account, "password_reset")
            except ValueError:
                pass
        return Response(
            {"detail": "If the account exists, a recovery code has been sent."}
        )


class ConfirmPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = IdentityService.find_account(
            serializer.validated_data["identifier"]
        )
        if not account:
            raise ValidationError({"code": "The code is invalid or expired."})
        try:
            IdentityService.reset_password(
                account,
                serializer.validated_data["code"],
                serializer.validated_data["new_password"],
            )
        except ValueError as exc:
            raise ValidationError({"code": str(exc)}) from exc
        return Response({"detail": "Password reset successfully."})


class RequestPhoneLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = IdentityService.find_account(
            serializer.validated_data["identifier"]
        )
        if account and account.phone_number:
            try:
                IdentityService.issue_code(account, "phone_login")
            except ValueError:
                pass
        return Response(
            {"detail": "If the account exists, a login code has been sent."}
        )


class ConfirmPhoneLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PhoneLoginConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = IdentityService.find_account(
            serializer.validated_data["phone_number"]
        )
        if not account:
            raise ValidationError({"code": "The code is invalid or expired."})
        try:
            IdentityService.consume_code(
                account,
                "phone_login",
                serializer.validated_data["code"],
            )
        except ValueError as exc:
            raise ValidationError({"code": str(exc)}) from exc
        profile = account.profile
        if profile.verification_level < 1:
            profile.verification_level = 1
            profile.save(update_fields=["verification_level"])
        refresh = RefreshToken.for_user(account)
        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh)}
        )

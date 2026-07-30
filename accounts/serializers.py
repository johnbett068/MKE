from django.db import transaction
from rest_framework import serializers

from wallets.models import Wallet
from .models import Account, AccountRole, Profile, Role


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["avatar", "address", "verification_level"]
        read_only_fields = ["verification_level"]


class AccountSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            "id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "profile",
            "roles",
        ]

    def get_roles(self, account):
        return list(
            account.roles.filter(is_active=True, status="approved")
            .values_list("role__name", flat=True)
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Account
        fields = [
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "password",
        ]

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        account = Account.objects.create_user(password=password, **validated_data)
        Profile.objects.create(account=account)
        customer_role, _ = Role.objects.get_or_create(
            name="customer",
            defaults={"description": "Requests services on the platform."},
        )
        AccountRole.objects.create(
            account=account,
            role=customer_role,
            status="approved",
        )
        Wallet.objects.create(account=account, role=customer_role)
        return account


class CodeRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=254)


class CodeVerifySerializer(serializers.Serializer):
    code = serializers.RegexField(r"^\d{6}$")


class PasswordResetConfirmSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=254)
    code = serializers.RegexField(r"^\d{6}$")
    new_password = serializers.CharField(write_only=True, min_length=8)


class PhoneLoginConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    code = serializers.RegexField(r"^\d{6}$")

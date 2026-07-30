from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from wallets.models import Wallet
from .models import Account, AccountRole, Profile
from unittest.mock import patch


class RegistrationTests(APITestCase):
    def test_registration_creates_customer_foundation(self):
        response = self.client.post(
            reverse("account-register"),
            {
                "email": "customer@example.com",
                "phone_number": "+254700000001",
                "first_name": "Amina",
                "last_name": "Test",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account = Account.objects.get(email="customer@example.com")
        self.assertTrue(Profile.objects.filter(account=account).exists())
        self.assertTrue(
            AccountRole.objects.filter(
                account=account,
                role__name="customer",
                status="approved",
            ).exists()
        )
        self.assertTrue(
            Wallet.objects.filter(account=account, role__name="customer").exists()
        )
        self.assertNotIn("password", response.data)

    @patch("accounts.services.secrets.randbelow", return_value=123456)
    def test_phone_verification_and_password_recovery(self, _random):
        account = Account.objects.create_user(
            "identity@example.com",
            "OriginalPass123!",
            phone_number="+254700000099",
        )
        Profile.objects.create(account=account)
        self.client.force_authenticate(account)
        response = self.client.post("/api/v1/accounts/phone/request-code/")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/api/v1/accounts/phone/verify/",
            {"code": "123456"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        account.profile.refresh_from_db()
        self.assertEqual(account.profile.verification_level, 1)

        self.client.force_authenticate(None)
        response = self.client.post(
            "/api/v1/accounts/password/request-reset/",
            {"identifier": account.phone_number},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            "/api/v1/accounts/password/confirm-reset/",
            {
                "identifier": account.phone_number,
                "code": "123456",
                "new_password": "ChangedPass123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        account.refresh_from_db()
        self.assertTrue(account.check_password("ChangedPass123!"))

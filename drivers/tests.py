from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from accounts.models import Account, Profile
from rides.models import Vehicle
from wallets.models import Wallet
from .models import Driver, DriverApplication, DriverDocument
from .services import DriverOnboardingService


class DriverOnboardingTests(APITestCase):
    def setUp(self):
        self.applicant = Account.objects.create_user(
            "applicant@example.com",
            "StrongPass123!",
            phone_number="+254700000010",
        )
        Profile.objects.create(
            account=self.applicant,
            verification_level=1,
        )
        self.admin = Account.objects.create_superuser(
            "admin@example.com",
            "StrongPass123!",
        )
        self.application = DriverApplication.objects.create(
            user=self.applicant,
            national_id_number="12345678",
            driving_license_number="DL-001",
            vehicle_type="car",
            vehicle_make="Toyota",
            vehicle_model="Axio",
            vehicle_year=2018,
            vehicle_color="Silver",
            license_plate="KDA 001A",
        )
        for document_type in (
            "national_id",
            "driver_license",
            "vehicle_registration",
        ):
            DriverDocument.objects.create(
                account=self.applicant,
                document_type=document_type,
                document_number=f"{document_type}-001",
                file=SimpleUploadedFile(
                    f"{document_type}.gif",
                    b"GIF89a",
                    content_type="image/gif",
                ),
                expires_at=date.today() + timedelta(days=365),
                status="approved",
                reviewed_by=self.admin,
            )

    def test_approval_creates_driver_vehicle_role_and_wallet(self):
        DriverOnboardingService.review_application(
            self.application,
            self.admin,
            "approved",
        )
        self.assertTrue(Driver.objects.filter(user=self.applicant).exists())
        self.assertTrue(
            Vehicle.objects.filter(
                driver=self.applicant,
                license_plate="KDA 001A",
            ).exists()
        )
        self.assertTrue(
            self.applicant.roles.filter(
                role__name="driver",
                status="approved",
            ).exists()
        )
        self.assertTrue(
            Wallet.objects.filter(
                account=self.applicant,
                role__name="driver",
            ).exists()
        )

    def test_approved_driver_can_go_online_and_heartbeat(self):
        DriverOnboardingService.review_application(
            self.application,
            self.admin,
            "approved",
        )
        self.client.force_authenticate(self.applicant)
        response = self.client.post(
            "/api/v1/drivers/presence/online/",
            {"latitude": -0.7813, "longitude": 35.3416},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["is_online"])
        self.assertTrue(response.data["is_available"])
        response = self.client.post(
            "/api/v1/drivers/presence/heartbeat/",
            {"latitude": -0.7800, "longitude": 35.3500},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

from django.test import TestCase, override_settings

from accounts.models import Account


class OperationsDashboardTests(TestCase):
    def test_dashboard_requires_staff_and_renders_for_admin(self):
        response = self.client.get("/operations/")
        self.assertEqual(response.status_code, 302)
        admin = Account.objects.create_superuser(
            "ops@example.com",
            "StrongPass123!",
        )
        self.client.force_login(admin)
        response = self.client.get("/operations/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Operations overview")


class HealthEndpointTests(TestCase):
    @override_settings(REDIS_URL=None)
    def test_health_endpoint_is_public_and_checks_database(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "checks": {"database": True, "redis": True},
            },
        )


class CorsPreflightTests(TestCase):
    def test_flutter_web_otp_preflight_allows_dynamic_localhost_origin(self):
        response = self.client.options(
            "/api/v1/accounts/phone-login/request/",
            HTTP_ORIGIN="http://localhost:54321",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS=(
                "content-type, authorization, x-csrftoken"
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "http://localhost:54321",
        )
        self.assertIn("POST", response.headers["access-control-allow-methods"])
        allowed_headers = response.headers["access-control-allow-headers"].lower()
        self.assertIn("content-type", allowed_headers)
        self.assertIn("authorization", allowed_headers)
        self.assertIn("x-csrftoken", allowed_headers)

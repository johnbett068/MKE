from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from core.management.commands.check_production_readiness import (
    collect_configuration_errors,
)


class ProductionReadinessTests(SimpleTestCase):
    @override_settings(
        DEBUG=False,
        SECRET_KEY="production-secret-with-sufficient-entropy",
        ALLOWED_HOSTS=["api.example.com"],
        SMS_BACKEND="http",
        CORS_ALLOWED_ORIGINS=["https://ops.example.com"],
        SECURE_HSTS_SECONDS=31536000,
        SECURE_SSL_REDIRECT=True,
    )
    def test_complete_secure_environment_passes_configuration_validation(self):
        environment = {
            "DJANGO_SECRET_KEY": "production-secret-with-sufficient-entropy",
            "JWT_SIGNING_KEY": "independent-jwt-signing-secret",
            "DATABASE_URL": "postgresql://mke:secret@db:5432/mke",
            "REDIS_URL": "redis://redis:6379/0",
            "ROUTING_API_URL": "https://routing.example.com",
            "SMS_API_URL": "https://sms.example.com/send",
            "SMS_API_KEY": "sms-secret",
            "SMS_SENDER_ID": "MKE",
            "MPESA_CONSUMER_KEY": "consumer",
            "MPESA_CONSUMER_SECRET": "consumer-secret",
            "MPESA_SHORTCODE": "123456",
            "MPESA_PASSKEY": "passkey",
            "MPESA_STK_CALLBACK_URL": "https://api.example.com/callback",
            "MPESA_CALLBACK_TOKEN": "callback-secret",
            "DOMAIN": "api.example.com",
            "POSTGRES_DB": "mke",
            "POSTGRES_USER": "mke",
            "POSTGRES_PASSWORD": "database-secret",
        }
        with patch.dict("os.environ", environment, clear=True):
            self.assertEqual(collect_configuration_errors(), [])

    @override_settings(DEBUG=True)
    def test_development_environment_is_rejected(self):
        errors = collect_configuration_errors(environ={})
        self.assertTrue(any("Missing environment variables" in item for item in errors))
        self.assertTrue(any("DJANGO_DEBUG" in item for item in errors))

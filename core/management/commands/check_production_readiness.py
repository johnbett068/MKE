import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


REQUIRED_ENVIRONMENT = (
    "DJANGO_SECRET_KEY",
    "JWT_SIGNING_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "ROUTING_API_URL",
    "SMS_API_URL",
    "SMS_API_KEY",
    "SMS_SENDER_ID",
    "MPESA_CONSUMER_KEY",
    "MPESA_CONSUMER_SECRET",
    "MPESA_SHORTCODE",
    "MPESA_PASSKEY",
    "MPESA_STK_CALLBACK_URL",
    "MPESA_CALLBACK_TOKEN",
    "DOMAIN",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)


def collect_configuration_errors(environ=None):
    if environ is None:
        environ = os.environ
    errors = []
    missing = [name for name in REQUIRED_ENVIRONMENT if not environ.get(name)]
    if missing:
        errors.append(f"Missing environment variables: {', '.join(missing)}")
    if settings.DEBUG:
        errors.append("DJANGO_DEBUG must be false.")
    if settings.SECRET_KEY.startswith("development-only"):
        errors.append("DJANGO_SECRET_KEY is still the development fallback.")
    if "*" in settings.ALLOWED_HOSTS or not settings.ALLOWED_HOSTS:
        errors.append("DJANGO_ALLOWED_HOSTS must contain explicit production hosts.")
    if settings.SMS_BACKEND != "http":
        errors.append("SMS_BACKEND must be 'http' for the production adapter.")
    database_url = environ.get("DATABASE_URL", "")
    if database_url and urlparse(database_url).scheme not in {
        "postgres",
        "postgresql",
    }:
        errors.append("DATABASE_URL must use PostgreSQL.")
    for name in ("ROUTING_API_URL", "MPESA_STK_CALLBACK_URL", "SMS_API_URL"):
        value = environ.get(name, "")
        if value and urlparse(value).scheme != "https":
            errors.append(f"{name} must use HTTPS.")
    if any(
        origin.startswith(("http://localhost", "http://127.0.0.1"))
        for origin in settings.CORS_ALLOWED_ORIGINS
    ):
        errors.append("Production CORS origins must not contain localhost.")
    if settings.SECURE_HSTS_SECONDS < 31536000:
        errors.append("DJANGO_SECURE_HSTS_SECONDS must be at least 31536000.")
    if not settings.SECURE_SSL_REDIRECT:
        errors.append("DJANGO_SECURE_SSL_REDIRECT must be enabled.")
    return errors


def collect_database_errors():
    if connection.vendor != "postgresql":
        return ["The active database connection is not PostgreSQL."]
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis')"
            )
            if not cursor.fetchone()[0]:
                return ["The PostGIS extension is not installed."]
    except Exception as exc:
        return [f"Production database check failed: {exc}"]
    return []


class Command(BaseCommand):
    help = "Fail unless MKE's production environment is safe and complete."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-database",
            action="store_true",
            help="Validate environment only (intended for image build checks).",
        )

    def handle(self, *args, **options):
        errors = collect_configuration_errors()
        if not options["skip_database"]:
            errors.extend(collect_database_errors())
        if errors:
            details = "\n".join(f"  - {error}" for error in errors)
            raise CommandError(f"Production readiness failed:\n{details}")
        self.stdout.write(
            self.style.SUCCESS("MKE production readiness checks passed.")
        )

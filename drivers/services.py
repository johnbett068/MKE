from datetime import date

from django.db import transaction
from django.db import models
from django.utils import timezone

from accounts.models import AccountRole, Role
from rides.models import Trip, Vehicle
from wallets.models import Wallet

from .models import Driver, DriverDocument


REQUIRED_DOCUMENTS = {
    "national_id",
    "driver_license",
    "vehicle_registration",
}


class DriverOnboardingService:
    @staticmethod
    @transaction.atomic
    def review_document(document, reviewer, status, comment=""):
        if status not in {"approved", "rejected"}:
            raise ValueError("Status must be approved or rejected.")
        document.status = status
        document.reviewed_by = reviewer
        document.reviewed_at = timezone.now()
        document.review_comment = comment
        document.save(
            update_fields=[
                "status", "reviewed_by", "reviewed_at", "review_comment"
            ]
        )
        return document

    @staticmethod
    def missing_requirements(account):
        approved = set(
            DriverDocument.objects.filter(
                account=account,
                status="approved",
            ).filter(
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=date.today())
            ).values_list("document_type", flat=True)
        )
        return REQUIRED_DOCUMENTS - approved

    @classmethod
    @transaction.atomic
    def review_application(cls, application, reviewer, status, comment=""):
        if status not in {"approved", "rejected"}:
            raise ValueError("Status must be approved or rejected.")
        if status == "approved":
            missing = cls.missing_requirements(application.user)
            if missing:
                raise ValueError(
                    f"Required approved documents are missing: {', '.join(sorted(missing))}."
                )
        application.status = status
        application.reviewed_by = reviewer
        application.reviewed_at = timezone.now()
        application.review_comment = comment
        application.save(
            update_fields=[
                "status", "reviewed_by", "reviewed_at", "review_comment"
            ]
        )
        if status == "approved":
            role = Role.objects.get(name="driver")
            AccountRole.objects.update_or_create(
                account=application.user,
                role=role,
                defaults={"status": "approved", "is_active": True},
            )
            Driver.objects.update_or_create(
                user=application.user,
                defaults={
                    "car_model": (
                        f"{application.vehicle_make} {application.vehicle_model}"
                    ),
                    "license_plate": application.license_plate,
                },
            )
            Vehicle.objects.update_or_create(
                license_plate=application.license_plate,
                defaults={
                    "driver": application.user,
                    "type": application.vehicle_type,
                    "make": application.vehicle_make,
                    "model": application.vehicle_model,
                    "year": application.vehicle_year,
                    "color": application.vehicle_color,
                    "is_active": True,
                },
            )
            Wallet.objects.get_or_create(account=application.user, role=role)
        return application


class DriverPresenceService:
    @staticmethod
    def ensure_eligible(user):
        application = getattr(user, "driver_application", None)
        if not application or application.status != "approved":
            raise PermissionError("An approved driver application is required.")
        if DriverOnboardingService.missing_requirements(user):
            raise PermissionError("Required driver documents are not current.")
        if not Vehicle.objects.filter(driver=user, is_active=True).exists():
            raise PermissionError("An active vehicle is required.")
        return user.driver_profile

    @classmethod
    @transaction.atomic
    def go_online(cls, user, latitude, longitude):
        driver = cls.ensure_eligible(user)
        active_trip = Trip.objects.filter(
            driver=user,
            status__in=["accepted", "in_progress"],
        ).exists()
        driver.is_online = True
        driver.is_available = not active_trip
        driver.current_latitude = latitude
        driver.current_longitude = longitude
        driver.last_seen = timezone.now()
        driver.save(
            update_fields=[
                "is_online", "is_available", "current_latitude",
                "current_longitude", "last_seen",
            ]
        )
        return driver

    @staticmethod
    def go_offline(user):
        driver = user.driver_profile
        if Trip.objects.filter(
            driver=user, status__in=["accepted", "in_progress"]
        ).exists():
            raise ValueError("A driver with an active trip cannot go offline.")
        driver.mark_offline()
        return driver

    @staticmethod
    def heartbeat(user, latitude, longitude):
        driver = user.driver_profile
        if not driver.is_online:
            raise ValueError("Driver is offline.")
        driver.current_latitude = latitude
        driver.current_longitude = longitude
        driver.last_seen = timezone.now()
        driver.save(
            update_fields=[
                "current_latitude", "current_longitude", "last_seen"
            ]
        )
        return driver

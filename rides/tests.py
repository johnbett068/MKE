from datetime import date, timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone

from accounts.models import Account, AccountRole, Role
from commissions.models import CommissionRule
from core.models import Location
from core.models import EventOutbox
from drivers.models import Driver
from pricing.models import PricingRule
from wallets.models import Wallet
from .models import Ride, Trip, TripCancellation, TripOffer


class TripApiTests(APITestCase):
    def setUp(self):
        self.customer_role = Role.objects.get(name="customer")
        self.driver_role = Role.objects.get(name="driver")
        self.customer = Account.objects.create_user(
            "customer@example.com", "StrongPass123!"
        )
        self.other_customer = Account.objects.create_user(
            "other@example.com", "StrongPass123!"
        )
        self.driver_user = Account.objects.create_user(
            "driver@example.com", "StrongPass123!"
        )
        AccountRole.objects.create(
            account=self.customer,
            role=self.customer_role,
            status="approved",
        )
        AccountRole.objects.create(
            account=self.driver_user,
            role=self.driver_role,
            status="approved",
        )
        Wallet.objects.create(account=self.customer, role=self.customer_role)
        self.driver_wallet = Wallet.objects.create(
            account=self.driver_user, role=self.driver_role
        )
        self.driver = Driver.objects.create(
            user=self.driver_user,
            car_model="Toyota",
            license_plate="KAA 001A",
            is_online=True,
            is_available=True,
            current_latitude=-0.7813,
            current_longitude=35.3416,
        )
        self.origin = Location.objects.create(
            country="Kenya", county="Bomet", town="Bomet", zone="Town"
        )
        self.destination = Location.objects.create(
            country="Kenya", county="Bomet", town="Bomet", zone="CBD"
        )
        PricingRule.objects.create(
            city="Bomet",
            service_type="ride",
            base_fare=Decimal("100.00"),
            per_km_rate=Decimal("20.00"),
            per_minute_rate=Decimal("2.00"),
        )
        CommissionRule.objects.create(
            service_type="ride",
            role=self.driver_role,
            percentage=Decimal("10.00"),
            flat_fee=Decimal("0.00"),
            effective_from=date.today(),
        )

    def request_trip(self):
        self.client.force_authenticate(self.customer)
        quote_response = self.client.post(
            "/api/v1/trips/quotes/",
            {
                "origin": self.origin.id,
                "destination": self.destination.id,
                "service_type": "ride",
                "pickup_latitude": "-0.7813",
                "pickup_longitude": "35.3416",
                "dropoff_latitude": "-0.7800",
                "dropoff_longitude": "35.3500",
            },
            format="json",
        )
        self.assertEqual(
            quote_response.status_code,
            status.HTTP_201_CREATED,
            quote_response.data,
        )
        response = self.client.post(
            "/api/v1/trips/",
            {
                "quote_id": quote_response.data["id"],
                "payment_method": "cash",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return Trip.objects.get(pk=response.data["id"])

    def test_customer_cannot_read_another_customers_trip(self):
        trip = self.request_trip()
        self.client.force_authenticate(self.other_customer)
        response = self.client.get(f"/api/v1/trips/{trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unapproved_account_cannot_view_offers(self):
        self.request_trip()
        self.client.force_authenticate(self.other_customer)
        response = self.client.get("/api/v1/trips/offers/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cash_ride_lifecycle_records_commission_debt(self):
        trip = self.request_trip()
        offer = TripOffer.objects.get(trip=trip, driver=self.driver_user)
        self.client.force_authenticate(self.driver_user)
        self.assertEqual(
            self.client.post(
                f"/api/v1/trips/offers/{offer.id}/accept/"
            ).status_code,
            status.HTTP_200_OK,
        )
        arrived = self.client.post(f"/api/v1/trips/{trip.id}/arrived/")
        self.assertEqual(arrived.status_code, status.HTTP_200_OK, arrived.data)
        self.client.force_authenticate(self.customer)
        detail = self.client.get(f"/api/v1/trips/{trip.id}/")
        pin = detail.data["start_pin"]
        self.client.force_authenticate(self.driver_user)
        wrong_pin = self.client.post(
            f"/api/v1/trips/{trip.id}/start/",
            {"pin": "9999" if pin != "9999" else "0000"},
            format="json",
        )
        self.assertEqual(wrong_pin.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.client.post(
                f"/api/v1/trips/{trip.id}/start/",
                {"pin": pin},
                format="json",
            ).status_code,
            status.HTTP_200_OK,
        )
        response = self.client.post(
            f"/api/v1/trips/{trip.id}/complete/",
            {"distance_km": "5.00", "duration_minutes": "10.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        trip.refresh_from_db()
        self.driver_wallet.refresh_from_db()
        ride = Ride.objects.get(trip=trip)
        self.assertEqual(trip.status, "completed")
        self.assertEqual(trip.fare, Decimal("220.00"))
        self.assertEqual(ride.commission_amount, Decimal("22.00"))
        self.assertEqual(self.driver_wallet.debt_balance, Decimal("22.00"))
        self.driver.refresh_from_db()
        self.assertTrue(self.driver.is_available)
        self.assertTrue(
            {
                "offer_received",
                "driver_accepted",
                "driver_arrived",
                "trip_started",
                "trip_completed",
            }.issubset(
                set(EventOutbox.objects.values_list("event_type", flat=True))
            )
        )

    def test_late_customer_cancellation_records_cash_fee(self):
        trip = self.request_trip()
        offer = TripOffer.objects.get(trip=trip, driver=self.driver_user)
        self.client.force_authenticate(self.driver_user)
        self.client.post(f"/api/v1/trips/offers/{offer.id}/accept/")
        Trip.objects.filter(pk=trip.pk).update(
            accepted_at=timezone.now() - timedelta(minutes=3)
        )
        self.client.force_authenticate(self.customer)
        response = self.client.post(
            f"/api/v1/trips/{trip.id}/cancel/",
            {"reason": "Plans changed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        cancellation = TripCancellation.objects.get(trip=trip)
        self.assertEqual(cancellation.fee_amount, Decimal("100.00"))
        self.assertEqual(cancellation.fee_status, "due")

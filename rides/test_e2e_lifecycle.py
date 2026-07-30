from datetime import date
from decimal import Decimal

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import Account, AccountRole, Role
from commissions.models import CommissionRule
from core.models import EventOutbox, Location
from drivers.models import Driver
from making_life_easier.asgi import application
from payments.models import PaymentIntent
from payments.services import PaymentService
from pricing.models import PricingRule
from rides.models import Ride, Trip, TripOffer
from wallets.models import Wallet


class FakeMpesaGateway:
    def initiate_stk_push(self, intent):
        return {
            "CheckoutRequestID": f"e2e-{intent.public_id}",
            "MerchantRequestID": f"e2e-merchant-{intent.public_id}",
        }


class CompleteTripLifecycleE2ETest(TransactionTestCase):
    """The multi-user path exercised by the two Flutter applications."""

    reset_sequences = True

    def setUp(self):
        self.customer_role, _ = Role.objects.get_or_create(
            name="customer",
            defaults={"description": "Customer"},
        )
        self.driver_role, _ = Role.objects.get_or_create(
            name="driver",
            defaults={"description": "Driver"},
        )
        self.customer = Account.objects.create_user(
            "e2e-customer@mke.test",
            "StrongPass123!",
            phone_number="+254700000101",
        )
        self.driver_user = Account.objects.create_user(
            "e2e-driver@mke.test",
            "StrongPass123!",
            phone_number="+254700000102",
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
            account=self.driver_user,
            role=self.driver_role,
        )
        Driver.objects.create(
            user=self.driver_user,
            car_model="Toyota Axio",
            license_plate="KDA 404E",
            is_online=True,
            is_available=True,
            current_latitude=-0.7813,
            current_longitude=35.3416,
        )
        self.origin = Location.objects.create(
            country="Kenya",
            county="Bomet",
            town="Bomet",
            zone="Town",
            latitude=-0.7813,
            longitude=35.3416,
        )
        self.destination = Location.objects.create(
            country="Kenya",
            county="Bomet",
            town="Bomet",
            zone="Equity",
            latitude=-0.7790,
            longitude=35.3500,
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

    @staticmethod
    def headers(user):
        token = str(AccessToken.for_user(user))
        return [(b"authorization", f"Bearer {token}".encode())]

    def test_quote_dispatch_websocket_trip_and_mpesa_debt_settlement(self):
        async def scenario():
            driver_socket = WebsocketCommunicator(
                application,
                "/ws/v1/drivers/me/",
                headers=self.headers(self.driver_user),
            )
            connected, _ = await driver_socket.connect()
            self.assertTrue(connected)
            self.assertEqual(
                (await driver_socket.receive_json_from())["type"],
                "connection_ready",
            )

            def create_trip_through_api():
                client = APIClient()
                client.force_authenticate(self.customer)
                quote = client.post(
                    "/api/v1/trips/quotes/",
                    {
                        "origin": self.origin.id,
                        "destination": self.destination.id,
                        "service_type": "ride",
                        "pickup_latitude": "-0.7813",
                        "pickup_longitude": "35.3416",
                        "dropoff_latitude": "-0.7790",
                        "dropoff_longitude": "35.3500",
                    },
                    format="json",
                )
                self.assertEqual(quote.status_code, 201, quote.data)
                trip = client.post(
                    "/api/v1/trips/",
                    {"quote_id": quote.data["id"], "payment_method": "cash"},
                    format="json",
                )
                self.assertEqual(trip.status_code, 201, trip.data)
                return trip.data["id"], trip.data["start_pin"]

            trip_id, pin = await database_sync_to_async(
                create_trip_through_api,
                thread_sensitive=True,
            )()
            offer_event = await driver_socket.receive_json_from(timeout=3)
            self.assertEqual(offer_event["type"], "offer_received")
            offer_id = offer_event["data"]["offer_id"]

            await driver_socket.send_json_to(
                {
                    "schema_version": "1.0",
                    "type": "offer_accept",
                    "request_id": "e2e-accept",
                    "data": {"offer_id": offer_id},
                }
            )
            accepted = await driver_socket.receive_json_from()
            self.assertEqual(accepted["type"], "command_succeeded")
            self.assertEqual(accepted["data"]["status"], "accepted")

            for command, data, expected in [
                ("driver_arrived", {"trip_id": trip_id}, "accepted"),
                (
                    "trip_start",
                    {"trip_id": trip_id, "pin": pin},
                    "in_progress",
                ),
                (
                    "trip_complete",
                    {
                        "trip_id": trip_id,
                        "distance_km": "5.00",
                        "duration_minutes": "10.00",
                    },
                    "completed",
                ),
            ]:
                await driver_socket.send_json_to(
                    {
                        "schema_version": "1.0",
                        "type": command,
                        "request_id": f"e2e-{command}",
                        "data": data,
                    }
                )
                response = await driver_socket.receive_json_from()
                self.assertEqual(response["type"], "command_succeeded", response)
                self.assertEqual(response["data"]["status"], expected)

            await driver_socket.disconnect()

            def settle_debt():
                trip = Trip.objects.get(pk=trip_id)
                ride = Ride.objects.get(trip=trip)
                self.driver_wallet.refresh_from_db()
                self.assertEqual(trip.status, "completed")
                self.assertEqual(ride.commission_amount, Decimal("22.00"))
                self.assertEqual(self.driver_wallet.debt_balance, Decimal("22.00"))
                intent = PaymentService.create_stk_intent(
                    account=self.driver_user,
                    wallet=self.driver_wallet,
                    purpose="cash_debt",
                    amount="22",
                    phone_number=self.driver_user.phone_number,
                    idempotency_key="e2e-debt-settlement",
                    gateway=FakeMpesaGateway(),
                )
                PaymentService.process_mpesa_callback(
                    {
                        "Body": {
                            "stkCallback": {
                                "CheckoutRequestID": intent.provider_reference,
                                "ResultCode": 0,
                                "ResultDesc": "Success",
                                "CallbackMetadata": {
                                    "Item": [
                                        {"Name": "Amount", "Value": 22},
                                        {
                                            "Name": "MpesaReceiptNumber",
                                            "Value": "E2E123",
                                        },
                                    ]
                                },
                            }
                        }
                    }
                )
                self.driver_wallet.refresh_from_db()
                intent.refresh_from_db()
                self.assertEqual(self.driver_wallet.debt_balance, Decimal("0.00"))
                self.assertEqual(intent.status, "completed")
                self.assertEqual(PaymentIntent.objects.count(), 1)
                self.assertEqual(TripOffer.objects.get(pk=offer_id).status, "accepted")
                self.assertTrue(
                    {
                        "offer_received",
                        "driver_accepted",
                        "driver_arrived",
                        "trip_started",
                        "trip_completed",
                    }.issubset(
                        set(
                            EventOutbox.objects.values_list(
                                "event_type",
                                flat=True,
                            )
                        )
                    )
                )

            await database_sync_to_async(settle_debt, thread_sensitive=True)()

        async_to_sync(scenario)()

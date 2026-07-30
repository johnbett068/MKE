from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import Account
from core.models import Location
from drivers.models import Driver
from making_life_easier.asgi import application
from rides.models import Ride, Trip


class RealtimeWebSocketTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.customer = Account.objects.create_user(
            "socket-customer@example.com",
            "StrongPass123!",
        )
        self.driver_user = Account.objects.create_user(
            "socket-driver@example.com",
            "StrongPass123!",
        )
        self.outsider = Account.objects.create_user(
            "socket-outsider@example.com",
            "StrongPass123!",
        )
        self.driver = Driver.objects.create(
            user=self.driver_user,
            car_model="Toyota Axio",
            license_plate="KWS 001A",
            is_online=True,
            is_available=False,
            current_latitude=-0.7813,
            current_longitude=35.3416,
        )
        origin = Location.objects.create(
            country="Kenya",
            county="Bomet",
            town="Bomet",
            zone="Town",
        )
        destination = Location.objects.create(
            country="Kenya",
            county="Bomet",
            town="Bomet",
            zone="CBD",
        )
        self.trip = Trip.objects.create(
            customer=self.customer,
            driver=self.driver_user,
            trip_type="ride",
            status="accepted",
            origin=origin,
            destination=destination,
        )
        Ride.objects.create(
            trip=self.trip,
            city="Bomet",
            pickup_latitude=-0.7813,
            pickup_longitude=35.3416,
            dropoff_latitude=-0.7800,
            dropoff_longitude=35.3500,
        )

    @staticmethod
    def headers(user):
        token = str(AccessToken.for_user(user))
        return [(b"authorization", f"Bearer {token}".encode())]

    def test_participant_receives_standardized_driver_location_event(self):
        async def scenario():
            trip_socket = WebsocketCommunicator(
                application,
                f"/ws/v1/trips/{self.trip.id}/",
                headers=self.headers(self.customer),
            )
            connected, _ = await trip_socket.connect()
            self.assertTrue(connected)
            ready = await trip_socket.receive_json_from()
            self.assertEqual(ready["type"], "connection_ready")

            driver_socket = WebsocketCommunicator(
                application,
                "/ws/v1/drivers/me/",
                headers=self.headers(self.driver_user),
            )
            connected, _ = await driver_socket.connect()
            self.assertTrue(connected)
            await driver_socket.receive_json_from()
            await driver_socket.send_json_to(
                {
                    "schema_version": "1.0",
                    "type": "driver_location_updated",
                    "data": {
                        "latitude": -0.7810,
                        "longitude": 35.3420,
                        "sequence": 12,
                    },
                }
            )
            acknowledgement = await driver_socket.receive_json_from()
            self.assertEqual(
                acknowledgement["type"],
                "driver_location_acknowledged",
            )
            location = await trip_socket.receive_json_from()
            self.assertEqual(location["schema_version"], "1.0")
            self.assertEqual(location["type"], "driver_location_updated")
            self.assertEqual(location["aggregate"]["id"], str(self.trip.id))
            self.assertEqual(location["data"]["latitude"], -0.781)
            await driver_socket.disconnect()
            await trip_socket.disconnect()

        async_to_sync(scenario)()

    def test_non_participant_cannot_subscribe_to_trip(self):
        async def scenario():
            socket = WebsocketCommunicator(
                application,
                f"/ws/v1/trips/{self.trip.id}/",
                headers=self.headers(self.outsider),
            )
            connected, close_code = await socket.connect()
            self.assertFalse(connected)
            self.assertEqual(close_code, 4403)

        async_to_sync(scenario)()

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist

from core.events import driver_group, event_envelope, trip_group
from rides.models import Trip
from rides.utils import estimate_eta_minutes, haversine_distance
from .models import Driver
from .services import DriverPresenceService


@database_sync_to_async
def update_driver_presence(user, latitude, longitude):
    driver = DriverPresenceService.heartbeat(user, latitude, longitude)
    trip = (
        Trip.objects.filter(
            driver=user,
            status__in=["accepted", "in_progress"],
        )
        .select_related("ride_details")
        .first()
    )
    if not trip:
        return driver, None
    details = trip.ride_details
    if trip.status == "accepted":
        target_lat = details.pickup_latitude
        target_lon = details.pickup_longitude
    else:
        target_lat = details.dropoff_latitude
        target_lon = details.dropoff_longitude
    distance = haversine_distance(
        latitude,
        longitude,
        target_lat,
        target_lon,
    )
    return driver, {
        "trip_id": trip.id,
        "latitude": latitude,
        "longitude": longitude,
        "distance_to_target_km": round(distance, 2),
        "eta_minutes": estimate_eta_minutes(distance),
    }


@database_sync_to_async
def execute_driver_command(user, event_type, data):
    from rides.services import DispatchService, RideService

    if event_type == "offer_accept":
        trip = DispatchService.accept_offer(int(data["offer_id"]), user)
        return {"trip_id": trip.id, "status": trip.status}
    if event_type == "offer_reject":
        from rides.models import TripOffer

        offer = TripOffer.objects.get(pk=int(data["offer_id"]), driver=user)
        DispatchService.reject_offer(offer, user)
        return {"offer_id": offer.id, "status": offer.status}
    trip_id = int(data["trip_id"])
    if event_type == "driver_arrived":
        trip = RideService.mark_arrived(trip_id, user)
    elif event_type == "trip_start":
        trip = RideService.start_trip(trip_id, user, str(data["pin"]))
    elif event_type == "trip_complete":
        trip = RideService.complete_trip(
            trip_id,
            user,
            data["distance_km"],
            data["duration_minutes"],
        )
    else:
        raise ValueError("Unsupported driver command.")
    return {"trip_id": trip.id, "status": trip.status}


class DriverStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.driver = await Driver.objects.filter(user_id=user.id).afirst()
        if not self.driver:
            await self.close(code=4403)
            return
        if not self.driver.is_online:
            await self.close(code=4409)
            return
        self.group_name = driver_group(user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(
            text_data=json.dumps(
                event_envelope(
                    "connection_ready",
                    "driver",
                    user.id,
                    {"stream": "driver"},
                )
            )
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            message = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            await self._protocol_error("Message must be valid JSON.")
            return
        if message.get("schema_version") != "1.0":
            await self._protocol_error("Unsupported schema_version.")
            return
        event_type = message.get("type")
        location_events = {"driver_heartbeat", "driver_location_updated"}
        command_events = {
            "offer_accept",
            "offer_reject",
            "driver_arrived",
            "trip_start",
            "trip_complete",
        }
        if event_type in command_events:
            try:
                result = await execute_driver_command(
                    self.scope["user"],
                    event_type,
                    message.get("data") or {},
                )
            except (
                KeyError,
                TypeError,
                ValueError,
                PermissionError,
                ObjectDoesNotExist,
            ) as exc:
                await self._protocol_error(str(exc))
                return
            await self.send(
                text_data=json.dumps(
                    event_envelope(
                        "command_succeeded",
                        "driver",
                        self.scope["user"].id,
                        {
                            "command": event_type,
                            "request_id": message.get("request_id"),
                            **result,
                        },
                    )
                )
            )
            return
        if event_type not in location_events:
            await self._protocol_error("Unsupported driver event type.")
            return
        data = message.get("data") or {}
        try:
            latitude = float(data["latitude"])
            longitude = float(data["longitude"])
            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            await self._protocol_error("Valid latitude and longitude are required.")
            return
        try:
            _, location = await update_driver_presence(
                self.scope["user"],
                latitude,
                longitude,
            )
        except ValueError as exc:
            await self._protocol_error(str(exc))
            return
        await self.send(
            text_data=json.dumps(
                event_envelope(
                    "driver_location_acknowledged",
                    "driver",
                    self.scope["user"].id,
                    {"sequence": data.get("sequence")},
                )
            )
        )
        if location:
            envelope = event_envelope(
                "driver_location_updated",
                "trip",
                location["trip_id"],
                location,
            )
            await self.channel_layer.group_send(
                trip_group(location["trip_id"]),
                {"type": "realtime.event", "envelope": envelope},
            )

    async def _protocol_error(self, detail):
        await self.send(
            text_data=json.dumps(
                event_envelope(
                    "protocol_error",
                    "driver",
                    self.scope["user"].id,
                    {"detail": detail},
                )
            )
        )

    async def realtime_event(self, event):
        await self.send(text_data=json.dumps(event["envelope"]))

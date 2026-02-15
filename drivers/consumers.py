# drivers/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import Driver

HEARTBEAT_TIMEOUT_SECONDS = 30


class DriverConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.driver_id = self.scope['url_route']['kwargs']['driver_id']
        self.group_name = f"driver_{self.driver_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.set_driver_online()

    async def disconnect(self, close_code):
        await self.set_driver_offline()

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "heartbeat":
            await self.update_heartbeat()

        elif data.get("type") == "location_update":
            await self.update_location(data)

    async def set_driver_online(self):
        driver = await sync_to_async(Driver.objects.get)(id=self.driver_id)
        driver.mark_online()

    async def set_driver_offline(self):
        driver = await sync_to_async(Driver.objects.get)(id=self.driver_id)
        driver.mark_offline()

    async def update_heartbeat(self):
        driver = await sync_to_async(Driver.objects.get)(id=self.driver_id)
        driver.update_heartbeat()

    async def update_location(self, data):
        """
        Update driver location and broadcast ETA if driver has an active ride.
        """
        driver = await sync_to_async(Driver.objects.get)(id=self.driver_id)

        driver.current_latitude = data.get("latitude")
        driver.current_longitude = data.get("longitude")
        driver.last_seen = timezone.now()
        await sync_to_async(driver.save)()

        # Check if driver has active ride
        from rides.models import Ride
        from rides.utils import haversine_distance, estimate_eta_minutes
        from rides.events import RideEventBroadcaster

        active_ride = await sync_to_async(
            Ride.objects.filter(
                driver=driver.user,
                status__in=['accepted', 'in_progress']
            ).first
        )()

        if not active_ride:
            return

        # Determine target point
        if active_ride.status == 'accepted':
            target_lat = active_ride.pickup_latitude
            target_lon = active_ride.pickup_longitude
        else:
            target_lat = active_ride.dropoff_latitude
            target_lon = active_ride.dropoff_longitude

        if not target_lat or not target_lon:
            return

        # Calculate distance and ETA
        distance = haversine_distance(
            driver.current_latitude,
            driver.current_longitude,
            target_lat,
            target_lon
        )
        eta = estimate_eta_minutes(distance)

        # Broadcast ETA update
        RideEventBroadcaster.broadcast(
            active_ride.id,
            "eta_update",
            {
                "distance_km": round(distance, 2),
                "eta_minutes": eta
            }
        )

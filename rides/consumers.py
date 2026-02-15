# rides/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class RideTrackingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time ride tracking.
    Drivers or backend can broadcast ride updates (location, status, etc.)
    to the customer in real-time.
    """

    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.room_group_name = f'ride_{self.ride_id}'

        # Join the ride-specific group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the ride-specific group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Optional: handle incoming messages from client.
        Currently pass-through; future expansion can handle location pings or custom events.
        """
        pass

    async def ride_event(self, event):
        """
        Receives broadcast events from server (e.g., location updates, ride status changes)
        and sends them to the connected WebSocket client.
        Event structure:
        {
            "type": "ride_event",
            "event_type": "<custom_event_type>",
            "data": {...}
        }
        """
        await self.send(text_data=json.dumps({
            "type": event.get("event_type"),
            "data": event.get("data"),
        }))

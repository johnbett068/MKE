import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import models

from core.events import event_envelope, trip_group
from .models import Trip


class TripStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.trip_id = int(self.scope["url_route"]["kwargs"]["trip_id"])
        self.group_name = trip_group(self.trip_id)
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return
        is_participant = await Trip.objects.filter(id=self.trip_id).filter(
            models.Q(customer_id=user.id) | models.Q(driver_id=user.id)
        ).aexists()
        if not is_participant:
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(
            text_data=json.dumps(
                event_envelope(
                    "connection_ready",
                    "trip",
                    self.trip_id,
                    {"stream": "trip"},
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
        await self.send(
            text_data=json.dumps(
                event_envelope(
                    "protocol_error",
                    "trip",
                    self.trip_id,
                    {"detail": "The trip stream is server-to-client only."},
                )
            )
        )

    async def realtime_event(self, event):
        await self.send(text_data=json.dumps(event["envelope"]))

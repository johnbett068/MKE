from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class RideEventBroadcaster:

    @staticmethod
    def broadcast(ride_id, event_type, data):

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"ride_{ride_id}",
            {
                "type": "ride_event",
                "event_type": event_type,
                "data": data,
            }
        )

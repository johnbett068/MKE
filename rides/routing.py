from django.urls import re_path

from .consumers import TripStreamConsumer


websocket_urlpatterns = [
    re_path(
        r"^ws/v1/trips/(?P<trip_id>\d+)/$",
        TripStreamConsumer.as_asgi(),
    ),
]

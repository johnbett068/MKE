from django.urls import re_path
from .consumers import RideTrackingConsumer

websocket_urlpatterns = [
    re_path(r'ws/ride/(?P<ride_id>\w+)/$', RideTrackingConsumer.as_asgi()),
]

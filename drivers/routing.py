from django.urls import re_path

from .consumers import DriverStreamConsumer


websocket_urlpatterns = [
    re_path(r"^ws/v1/drivers/me/$", DriverStreamConsumer.as_asgi()),
]

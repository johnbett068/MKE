import os
from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import drivers.routing  # Make sure this exists with websocket_urlpatterns

# Set default settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'making_life_easier.settings')

# Standard Django ASGI application for HTTP
django_asgi_app = get_asgi_application()

# Channels application
application = ProtocolTypeRouter({
    # Django's HTTP handling
    "http": django_asgi_app,

    # WebSocket handling
    "websocket": AuthMiddlewareStack(
        URLRouter(
            drivers.routing.websocket_urlpatterns
        )
    ),
})

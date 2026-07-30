import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'making_life_easier.settings')

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from core.websocket_auth import JWTAuthMiddleware  # noqa: E402
import drivers.routing  # noqa: E402
import rides.routing  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            drivers.routing.websocket_urlpatterns
            + rides.routing.websocket_urlpatterns
        )
    ),
})

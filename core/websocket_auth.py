from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


@database_sync_to_async
def _jwt_user(raw_token):
    authentication = JWTAuthentication()
    validated = authentication.get_validated_token(raw_token)
    return authentication.get_user(validated)


class JWTAuthMiddleware:
    """Authenticate WebSockets from an Authorization: Bearer header."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        authorization = headers.get(b"authorization", b"").decode()
        scope["user"] = AnonymousUser()
        if authorization.startswith("Bearer "):
            try:
                scope["user"] = await _jwt_user(authorization[7:])
            except Exception:
                scope["user"] = AnonymousUser()
        return await self.app(scope, receive, send)

from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from jwt import decode as jwt_decode
from django.conf import settings

User = get_user_model()

@database_sync_to_async
def get_user(token):
    try:
        # validate token (raises if invalid)
        UntypedToken(token)
        decoded = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = decoded.get("user_id") or decoded.get("user_id")  # depending on token payload
        user = User.objects.filter(id=user_id).first()
        return user
    except (TokenError, InvalidToken, Exception):
        return None

class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware to authenticate WebSocket connections by ?token=<JWT>
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        qs = parse_qs(query_string)
        token_list = qs.get("token", None)
        if token_list:
            token = token_list[0]
            user = await get_user(token)
            if user:
                scope["user"] = user
            else:
                scope["user"] = None
        else:
            # keep existing scope user (AnonymousUser) if any
            scope["user"] = None
        return await super().__call__(scope, receive, send)

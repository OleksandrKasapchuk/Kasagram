from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.middleware import BaseMiddleware

@database_sync_to_async
def get_user(token_key):
    try:
        return Token.objects.get(key=token_key).user
    except Token.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        # Шукаємо заголовок authorization (в Channels він у нижньому регістрі)
        if b'authorization' in headers:
            try:
                token_name, token_key = headers[b'authorization'].decode().split()
                if token_name == 'Token':
                    scope['user'] = await get_user(token_key)
            except Exception:
                scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
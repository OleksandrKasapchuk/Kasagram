# social_media/middleware.py
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.middleware import BaseMiddleware
import traceback

@database_sync_to_async
def get_user(token_key):
    try:
        return Token.objects.select_related('user').get(key=token_key).user
    except Token.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        try:
            headers = dict(scope['headers'])
            token_key = None
            raw_protocol_header = None

            # 1. Спроба для Android (класичний заголовок Authorization)
            if b'authorization' in headers:
                try:
                    token_name, token_key_val = headers[b'authorization'].decode().split()
                    if token_name == 'Token':
                        token_key = token_key_val
                except Exception:
                    pass

            # 2. Спроба для Next.js (через Sec-WebSocket-Protocol)
            if not token_key and b'sec-websocket-protocol' in headers:
                try:
                    raw_protocol_header = headers[b'sec-websocket-protocol'].decode()
                    # Парсимо, щоб знайти сам токен для бази даних
                    protocols = [p.strip() for p in raw_protocol_header.split(',')]
                    if 'Token' in protocols:
                        token_index = protocols.index('Token') + 1
                        if token_index < len(protocols):
                            token_key = protocols[token_index]
                except Exception as e:
                    print(f"❌ Помилка парсингу WebSocket протоколів: {e}")

            # 3. Кладимо юзера в scope
            if token_key:
                scope['user'] = await get_user(token_key)
            else:
                scope['user'] = AnonymousUser()

            # 4. 🔥 ВИПРАВЛЕНО ДЛЯ БРАУЗЕРА:
            # Замість усього сирого рядка з комою, повертаємо саме той токен,
            # який ми успішно дістали і за яким авторизували користувача.
            if raw_protocol_header and token_key:
                inner_send = send
                async def send_with_protocol(message):
                    if message["type"] == "websocket.accept":
                        # Передаємо саме обраний підпротокол (токен), а не весь рядок з комою
                        message["subprotocol"] = token_key
                    await inner_send(message)
                send = send_with_protocol

            return await super().__call__(scope, receive, send)

        except Exception as err:
            print("💥 КРИТИЧНА ПОМИЛКА В МІДЛВАРІ:")
            traceback.print_exc()
            return await super().__call__(scope, receive, send)
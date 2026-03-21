from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Переконайся, що шлях збігається з тим, що ти пишеш у JS
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
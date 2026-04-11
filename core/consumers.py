import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturaltime
import asyncio
from .mixins import *


class ChatConsumer(AsyncWebsocketConsumer, ChatDatabaseMixin):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name,self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        handlers = {
            'mark_as_read': self.handle_mark_read,
            'typing': self.handle_typing,
            'delete': self.handle_delete,
            'chat_message': self.handle_chat_message,
        }

        handler = handlers.get(action)
        if handler:
            await handler(data)

    async def handle_mark_read(self, data):
        await self.mark_messages_as_read(self.room_name, self.scope['user'])
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'messages_read_update', 'username': self.scope['user'].username}
        )

    async def handle_typing(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'username': self.scope['user'].username,
                'typing': data['typing']
            }
        )

    async def handle_delete(self, data):
        message_id = data['message_id']
        
        success = await self.delete_message_from_db(message_id, self.scope['user'])
        
        if success:
            # Розсилаємо всім сигнал на видалення
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_deleted',
                    'message_id': message_id
                }
            )
    
    async def handle_chat_message(self, data):
        content = data['message']
        username = data['username']
        parent_id = data.get('parent_id')
        msg_data = await self.save_message(username, self.room_name, content, parent_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'content': content,
                'username': username,
                'message_id': msg_data['id'],
                'timestamp': msg_data['timestamp'].strftime('%H:%M'),
                'parent_content': msg_data['parent_content'],
                'parent_username': msg_data['parent_username'],
                'temp_id': data.get('temp_id')
            }
        )
        recipient = await self.get_recipient(self.room_name, self.scope['user'].id)

        unread_cnt = await self.count_unread(recipient, self.room_name)

        await self.channel_layer.group_send(
            f"user_global_{recipient.id}", 
            {
                "type": "chat_notification",
                "message": content,
                "chat_id": self.room_name,
                "sender_name": username,
                "unread_count": unread_cnt
            }
        )

    # Обробка отриманого повідомлення групою
    async def chat_message(self, event):
        is_me = self.scope['user'].username == event['username']
        # Надсилаємо назад на фронтенд (в браузер)
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'content': event['content'],
            'username': event['username'],
            'message_id': event['message_id'],
            'is_me': is_me,
            'timestamp': event['timestamp'],
            'parent_content': event.get('parent_content'),
            'parent_username': event.get('parent_username'),
            'parent_id': event.get('parent_id'),
            'temp_id': event.get('temp_id')
        }))
    
    # Обробник події видалення для групи
    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'delete_message',
            'message_id': event['message_id']
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'username': event['username'],
            'typing': event['typing']
        }))
    
    
    async def messages_read_update(self, event):
        is_me = self.scope['user'].username == event['username']
    
        # Відправляємо клієнту сигнал, щоб JS оновив галочки
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'username': event['username'],
            'is_me': is_me
        }))


class GlobalConsumer(AsyncWebsocketConsumer, PresenceMixin):
    delays = {}

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            user_id = self.user.id
            
            # Створюємо задачу на "вимкнення" через 5 секунд
            task = asyncio.create_task(self.delayed_offline(user_id))
            GlobalConsumer.delays[user_id] = task

    async def delayed_offline(self, user_id):
        try:
            await asyncio.sleep(5)
            if user_id in GlobalConsumer.delays:
                # Важливо: використовуємо метод міксина
                await self.update_user_online(self.user, False) 
                await self.broadcast_status(False)
        except asyncio.CancelledError:
            pass # Це нормально, користувач просто перезайшов
        finally:
            GlobalConsumer.delays.pop(user_id, None)

    async def connect(self):
        await self.accept()
    
        self.user = self.scope['user']

        if self.user.is_authenticated:
            print(f"Global connected! Username: {self.user.username}")
            user_id = self.user.id
            
            # Ваша логіка з delays
            if user_id in GlobalConsumer.delays:
                GlobalConsumer.delays[user_id].cancel()
                del GlobalConsumer.delays[user_id]
            else:
                await self.update_user_online(self.scope['user'], True)
                await self.broadcast_status(True)
            
            self.user_group = f"user_global_{user_id}"
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            await self.channel_layer.group_add("global_presence", self.channel_name)
        else:
            # 2. Якщо користувач не авторизований, повідомляємо про це і закриваємо
            print("User not authenticated! Closing...")
            await self.send(text_data=json.dumps({"error": "Unauthorized"}))
            await self.close(code=4003)

    async def user_status_change(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def broadcast_status(self, is_online):
        recipient_ids = await self.get_notification_recipients(self.scope['user'])
        
        now = timezone.now()
        readable_time = str(naturaltime(now))
        
        event_data = {
            'type': 'user_status_change',
            'username': self.user.username,
            'is_online': is_online,
            'last_seen': readable_time if not is_online else "Online"
        }

        for user_id in recipient_ids:
            # Шлемо кожному другу в його "персональний канал"
            await self.channel_layer.group_send(
                f"user_global_{user_id}", 
                event_data
            )

    async def notification_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_notification",
            "message": event.get("message"),
            "unread_count": event.get("unread_count"),
            "actor_name": event.get("actor_name"),
            "actor_url": event.get("actor_url"),
            "actor_avatar": event.get("actor_avatar"),
            "target_url": event.get("target_url"),
        }))

    async def chat_notification(self, event):
        # Цей метод викликає сам Django, коли в групу прийшло повідомлення
        # Тепер ми просто пересилаємо це в браузер через WebSocket
        await self.send(text_data=json.dumps({
            "action": "new_message",
            "chat_id": event["chat_id"],
            "message": event["message"],
            "unread_count": event.get("unread_count"), 
            "sender_name": event.get("sender_name")
        }))
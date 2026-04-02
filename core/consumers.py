import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import Message, Chat
from auth_system.models import CustomUser
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturaltime
import asyncio


class ChatConsumer(AsyncWebsocketConsumer):
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

        if action == 'mark_as_read':
            await self.mark_messages_as_read()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'messages_read_update',
                    'username': self.scope['user'].username,
                }
            )
        elif action == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'username': self.scope['user'].username,
                    'typing': data['typing']
                }
            )
        elif action == 'delete':
            message_id = data['message_id']
            
            success = await self.delete_message_from_db(message_id)
            
            if success:
                # Розсилаємо всім сигнал на видалення
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': message_id
                    }
                )
        elif action == 'chat_message':
        
            message_text = data['message']
            username = data['username']
            parent_id = data.get('parent_id')
            msg_data = await self.save_message(username, self.room_name, message_text, parent_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_text,
                    'username': username,
                    'message_id': msg_data['id'],
                    'timestamp': msg_data['timestamp'].strftime('%H:%M'),
                    'parent_content': msg_data['parent_content'],
                    'parent_username': msg_data['parent_username']
                }
            )
            recipient = await self.get_recipient(self.room_name)

            unread_cnt = await self.count_unread(recipient, self.room_name)

            await self.channel_layer.group_send(
                f"user_global_{recipient.id}", 
                {
                    "type": "chat_notification",
                    "message": message_text,
                    "chat_id": self.room_name,
                    "sender_name": username,
                    "unread_count": unread_cnt # Додай це
                }
            )

    @database_sync_to_async
    def count_unread(self, recipient, chat_id):
        chat = Chat.objects.get(id=chat_id)
        return chat.messages.filter(is_read=False).exclude(user=recipient).count()

    # Обробка отриманого повідомлення групою
    async def chat_message(self, event):
        is_me = self.scope['user'].username == event['username']
        # Надсилаємо назад на фронтенд (в браузер)
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'message_id': event['message_id'],
            'is_me': is_me,
            'timestamp': event['timestamp'],
            'parent_content': event.get('parent_content'),
            'parent_username': event.get('parent_username'),
            'parent_id': event.get('parent_id'),
        }))
    
    @database_sync_to_async
    def get_recipient(self, chat_id):
        chat = Chat.objects.get(id=chat_id)
        # Повертає учасника, який не є поточним юзером
        return chat.participants.exclude(id=self.scope['user'].id).first()
    
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

    @database_sync_to_async
    def delete_message_from_db(self, message_id):
        try:
            user = self.scope['user']
            msg = Message.objects.get(id=message_id, user=user)
            msg.delete()
            return True
        except Message.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, username, chat_id, message, parent_id=None):
        user = CustomUser.objects.get(username=username)
        chat = Chat.objects.get(id=chat_id)
        parent = None
        
        if parent_id:
            try:
                parent = Message.objects.get(id=parent_id)
            except Message.DoesNotExist:
                parent = None
                
        msg = Message.objects.create(user=user, chat=chat, content=message, parent=parent)
        
        # Створюємо словник з даними, щоб не робити запитів у асинхронному коді
        result = {
            'id': msg.id,
            'timestamp': msg.timestamp,
            'parent_content': msg.parent.content if msg.parent else None,
            'parent_username': msg.parent.user.username if msg.parent else None,
        }
        return result
    
    async def messages_read_update(self, event):
        is_me = self.scope['user'].username == event['username']
    
        # Відправляємо клієнту сигнал, щоб JS оновив галочки
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'username': event['username'],
            'is_me': is_me
        }))
    
    @database_sync_to_async
    def mark_messages_as_read(self):
        Message.objects.filter(
            chat_id=self.room_name,
            is_read=False).exclude(user=self.scope['user']).update(is_read=True)


class GlobalConsumer(AsyncWebsocketConsumer):
    delays = {}

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            user_id = self.user.id
            
            # Створюємо задачу на "вимкнення" через 5 секунд
            task = asyncio.create_task(self.delayed_offline(user_id))
            GlobalConsumer.delays[user_id] = task

    async def delayed_offline(self, user_id):
        await asyncio.sleep(5) # Чекаємо 5 секунд
        
        # Якщо задача все ще в словнику (її не скасував connect)
        if user_id in GlobalConsumer.delays:
            await self.update_user_online(False)
            
            now = timezone.now()
            readable_time = str(naturaltime(now))
            await self.channel_layer.group_send(
                "global_presence",
                {
                    'type': 'user_status_change',
                    'username': self.user.username,
                    'is_online': False,
                    'last_seen': readable_time
                }
            )
            del GlobalConsumer.delays[user_id]

    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            user_id = self.user.id
            
            # ЯКЩО ЮЗЕР ПЕРЕЙШОВ НА НОВУ СТОРІНКУ:
            # Скасовуємо задачу на офлайн, бо він щойно підключився знову!
            if user_id in GlobalConsumer.delays:
                GlobalConsumer.delays[user_id].cancel()
                del GlobalConsumer.delays[user_id]
            else:
                # Якщо його не було в списку на вихід — значить він реально зайшов вперше
                await self.update_user_online(True)
                await self.channel_layer.group_send(
                    "global_presence",
                    {
                        'type': 'user_status_change',
                        'username': self.user.username,
                        'is_online': True
                    }
                )
            
            self.user_group = f"user_global_{user_id}"
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            await self.channel_layer.group_add("global_presence", self.channel_name)
            await self.accept()
    async def user_status_change(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def update_user_online(self, status):
        CustomUser.objects.filter(pk=self.user.pk).update(is_online=status, last_seen=timezone.now())
    
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
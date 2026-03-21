import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import Message, Chat
from auth_system.models import CustomUser
from django.utils import timezone


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

    # Отримання повідомлення від JS
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == 'typing':
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
        else:
            message_text = data['message']
            username = data['username']
            msg_obj_id = await self.save_message(username, self.room_name, message_text)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_text,
                    'username': username,
                    'message_id': msg_obj_id # Передаємо ID, щоб потім можна було видалити
                }
            )

    # Обробка отриманого повідомлення групою
    async def chat_message(self, event):
        # Надсилаємо назад на фронтенд (в браузер)
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'message_id': event['message_id']
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
    def save_message(self, username, chat_id, message):
        user = CustomUser.objects.get(username=username)
        chat = Chat.objects.get(id=chat_id)
        msg = Message.objects.create(user=user,chat=chat,content=message)
        return msg.id


class GlobalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            self.user_group = f"user_global_{self.user.id}"
            
            # Додаємо юзера в його персональну групу для нотіфікацій
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            
            # Додаємо в загальну групу "всіх", щоб бачити статуси інших
            await self.channel_layer.group_add("global_presence", self.channel_name)
            
            await self.accept()
            
            # Оновлюємо статус в БД
            await self.update_user_online(True)
            
            # Розсилаємо всім: "Юзер X зайшов на сайт"
            await self.channel_layer.group_send(
                "global_presence",
                {
                    'type': 'user_status_change',
                    'username': self.user.username,
                    'is_online': True
                }
            )

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.update_user_online(False)
            
            await self.channel_layer.group_send(
                "global_presence",
                {
                    'type': 'user_status_change',
                    'username': self.user.username,
                    'is_online': False
                }
            )
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
            await self.channel_layer.group_discard("global_presence", self.channel_name)

    async def user_status_change(self, event):
        # Відправляємо інфу про зміну статусу на фронтенд/апку
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
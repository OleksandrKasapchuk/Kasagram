import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Chat # Перевір назви своїх моделей
from auth_system.models import CustomUser


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Отримання повідомлення від JS
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data["action"]

        if action == 'delete':
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
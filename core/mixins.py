from channels.db import database_sync_to_async
from chat.models import Message, Chat
from auth_system.models import CustomUser
from django.utils import timezone

class ChatDatabaseMixin:
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
        
        return {
            'id': msg.id,
            'timestamp': msg.timestamp,
            'parent_content': msg.parent.content if msg.parent else None,
            'parent_username': msg.parent.user.username if msg.parent else None,
        }
    
    @database_sync_to_async
    def mark_messages_as_read(self, chat_id, user):
        return Message.objects.filter(
            chat_id=chat_id, 
            is_read=False
        ).exclude(user=user).update(is_read=True)

    @database_sync_to_async
    def get_recipient(self, chat_id, current_user_id):
        chat = Chat.objects.get(id=chat_id)
        return chat.participants.exclude(id=current_user_id).first()
    
    @database_sync_to_async
    def delete_message_from_db(self, message_id, user):
        try:
            msg = Message.objects.get(id=message_id, user=user)
            msg.delete()
            return True
        except Message.DoesNotExist:
            return False
    
    @database_sync_to_async
    def count_unread(self, recipient, chat_id):
        chat = Chat.objects.get(id=chat_id)
        return chat.messages.filter(is_read=False).exclude(user=recipient).count()


class PresenceMixin:
    @database_sync_to_async
    def update_user_online(self, user, status):
        CustomUser.objects.filter(pk=user.pk).update(is_online=status, last_seen=timezone.now())

    @database_sync_to_async
    def get_notification_recipients(self, user):
        recipient_ids = CustomUser.objects.filter(
            chats__participants=user
        ).exclude(id=user.id).values_list('id', flat=True).distinct()
        return list(recipient_ids)
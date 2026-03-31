from django.urls import reverse_lazy

from .models import Message
from django.templatetags.static import static
from post_system.mixins import *


class ChatMessageMixin:
    def get_serialized_messages(self, chat, request, oldest_id=None):
        messages = Message.objects.filter(chat=chat).select_related('user')
        
        if oldest_id and str(oldest_id).isdigit():
            messages = messages.filter(pk__lt=oldest_id).order_by('-pk')[:20]
        else:
            messages = messages.order_by('-pk')[:20]
            
        return [{
            'id': msg.pk,
            'content': msg.content,
            'is_user_message': msg.user == request.user,
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'username': msg.user.username,
            'avatar_url': msg.user.avatar.url if msg.user.avatar else static('images/default_avatar.png'),
            'delete_url': reverse_lazy('chat:delete_message', args=[msg.pk]),
            'is_user_message': msg.user == request.user,
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'is_read': msg.is_read,
            'parent_username': msg.parent.user.username if msg.parent else None,
            'parent_content': msg.parent.content if msg.parent else None,
        } for msg in messages][::-1] # Повертаємо у хронологічному порядку
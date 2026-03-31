from .models import Message
from post_system.mixins import *
from .serializers import MessageSerializer


class ChatMessageMixin:
    def get_serialized_messages(self, chat, request, oldest_id=None):
        messages = Message.objects.filter(chat=chat).select_related('user')
        
        if oldest_id and str(oldest_id).isdigit():
            messages = messages.filter(pk__lt=oldest_id).order_by('-pk')[:20]
        else:
            messages = messages.order_by('-pk')[:20]
        
        return MessageSerializer(messages, many=True, context={'request': self.request}).data
from rest_framework import serializers
from .models import Message, Chat
from users.serializers import UserSerializer
from common.utils import format_date


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    is_me = serializers.SerializerMethodField()

    formatted_time = serializers.SerializerMethodField()
    parent_id = serializers.PrimaryKeyRelatedField(source='parent', read_only=True)
    parent_content = serializers.ReadOnlyField(source='parent.content')
    parent_username = serializers.ReadOnlyField(source='parent.user.username')

    class Meta:
        model = Message
        fields = [
            'id', 'user', 'content', 'timestamp', 'formatted_time', 
            'is_read', 'is_me', 'parent_id', 'parent_content', 'parent_username',
        ]
    
    def get_is_me(self, obj):
        # Отримуємо юзера з контексту запиту
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False

    def get_formatted_time(self, obj):
        return obj.timestamp.strftime('%H:%M')
    


class ChatSerializer(serializers.ModelSerializer):
    participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        # Видаляємо загальний список participants, лишаємо тільки цільового юзера
        fields = ['id', 'participant', 'last_message', 'unread_count']

    def get_participant(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Отримуємо того, хто НЕ я
            user = obj.participants.exclude(id=request.user.id).first()
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'avatar_url': user.avatar.url if user.avatar else None,
                    'is_online': user.is_online, # Твоє поле з CustomUser
                    'last_seen': user.last_seen # Корисно для статусу "був у мережі"
                }
        return None

    def get_unread_count(self, obj):
        # Логіка підрахунку нечитаних для поточного юзера
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(user=user).count()
    
    def get_last_message(self, obj):
        # Отримуємо саме останнє повідомлення за часом
        msg = obj.messages.order_by('-timestamp').first()
        if msg:
            return {
                'content': msg.content,
                'formatted_time': format_date(msg.timestamp),
                'is_read': msg.is_read,
                'timestamp': msg.timestamp,
                # Можна додати прапорець, щоб знати, чи це я написав останній
                'is_me': msg.user == self.context['request'].user if 'request' in self.context else False
            }
        return None
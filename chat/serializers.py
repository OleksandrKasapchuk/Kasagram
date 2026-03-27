from rest_framework import serializers
from .models import Message, Chat
from auth_system.serializers import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    # Дані про повідомлення, на яке відповідаємо
    parent_id = serializers.PrimaryKeyRelatedField(source='parent', read_only=True)
    parent_content = serializers.ReadOnlyField(source='parent.content')
    parent_username = serializers.ReadOnlyField(source='parent.user.username')

    class Meta:
        model = Message
        fields = [
            'id', 'user', 'content', 'timestamp', 'is_read', 
            'parent_id', 'parent_content', 'parent_username'
        ]


class ChatSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'participants', 'last_message', 'unread_count']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-timestamp').first()
        if msg:
            return {
                'content': msg.content,
                'user': msg.user.username,
                'timestamp': msg.timestamp
            }
        return None

    def get_unread_count(self, obj):
        # Логіка підрахунку нечитаних для поточного юзера
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(user=user).count()
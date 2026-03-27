from rest_framework import serializers
from .models import *
from auth_system.serializers import UserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    # Хто саме зробив дію (лайкнув, прокоментував)
    actor_details = UserSerializer(source='actor', read_only=True)
    # Зручне текстове повідомлення та URL
    message = serializers.CharField(source='get_message', read_only=True)
    target_url = serializers.CharField(source='get_url', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'actor_details', 'type', 
            'post', 'comment', 'chat', 
            'message', 'target_url', 'created_at', 'is_read'
        ]
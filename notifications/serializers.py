from rest_framework import serializers
from .models import Notification
from users.serializers import UserBaseSerializer  # чи як там у тебе називається файл


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserBaseSerializer()
    
    # 🎯 Замість get_message просимо Django повернути human-лейбл з Choices
    message = serializers.ReadOnlyField(source='get_notification_type_display')
    
    type = serializers.CharField(source='notification_type')
    target_id = serializers.IntegerField(source='object_id')
    
    class Meta:
        model = Notification
        fields = [
            'id', 'actor', 'message', 'type', 
            'target_id', 'is_read', 'created_at'
        ]
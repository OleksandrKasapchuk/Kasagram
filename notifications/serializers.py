from rest_framework import serializers
from .models import *
from common.utils import format_date
from auth_system.serializers import UserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer()
    message = serializers.ReadOnlyField(source='get_message')
    target_url = serializers.ReadOnlyField(source='get_url')
    created_at_human = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'actor', 'message', 
            'target_url', 'is_read', 'created_at', 'created_at_human'
        ]

    def get_created_at_human(self, obj):
        return format_date(obj.created_at)
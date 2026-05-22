from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class NotificationAPIView(ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')[:10]


class MarkNotificationsReadView(APIView):
    # 🔐 Дозволяємо доступ тільки залогіненим користувачам
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Оновлюємо статус сповіщень
        user.notifications.filter(is_read=False).update(is_read=True)
        
        # Відправляємо оновлення в сокет (Django Channels)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_global_{user.id}",
            {
                "type": "notification_message",
                "unread_count": 0, 
            }
        )
        
        # DRF-style відповідь з HTTP 200 OK
        return Response({'success': True}, status=status.HTTP_200_OK)
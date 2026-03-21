from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class NotificationView(LoginRequiredMixin,ListView):
	model = Notification
	template_name = 'notifications/notifications.html'
	context_object_name = "notifications"
	def get_queryset(self):
		return Notification.objects.filter(user_id=self.kwargs["pk"]).order_by('-created_at')[:5]


def mark_notifications_as_read(request):
    # Твоя логіка mark_as_read...
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    # Відправляємо оновлення в сокет
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_global_{request.user.id}",
        {
            "type": "notification_message",
            "unread_count": 0, # Кажемо фронтенду: "Все, цифра 0"
            "message": "All read"
        }
    )
    return JsonResponse({'success': True})
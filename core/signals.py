from django.db.models.signals import post_save
from django.dispatch import receiver
from post_system.models import Like, Comment
from notifications.models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
from chat.models import Message
from notifications.models import Notification
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        actor = instance.user

        if actor != post.user:
            threshold = timezone.now() - timedelta(minutes=5)
            
            # Отримуємо ContentType для моделі Post
            post_type = ContentType.objects.get_for_model(post)
            
            # Шукаємо дублікат за останні 5 хвилин
            existing_notif = Notification.objects.filter(
                user=post.user,
                actor=actor,
                content_type=post_type,
                object_id=post.id,
                created_at__gte=threshold
            ).exists()

            if not existing_notif:
                Notification.objects.create(
                    user=post.user,
                    actor=actor,
                    target=post
                )

@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        actor = instance.user

        if actor != post.user:
            Notification.objects.create(
                user=post.user,
                actor=actor,
                target=instance
            )

@receiver(post_save, sender=Message)
def send_message_notification(sender, instance, created, **kwargs):
    if created:
        chat = instance.chat
        sender_user = instance.user
        recipient = chat.participants.exclude(id=sender_user.id).first()

        if recipient:
            Notification.objects.create(
                user=recipient,
                actor=sender_user,
                target=chat
            )

@receiver(post_save, sender=Notification)
def notify_on_new_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        unread_count = user.notifications.filter(is_read=False).count()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_global_{user.id}",
            {
                "type": "notification_message",
                "message": instance.get_message(),
                "unread_count": unread_count,
                "actor_name": instance.actor.username,
                "actor_url": reverse('user-info', kwargs={'pk': instance.actor.pk}),
                "actor_avatar": instance.actor.avatar.url if instance.actor.avatar else '/static/images/default_avatar.jpg',
                "target_url": instance.get_url(),
            }
        )
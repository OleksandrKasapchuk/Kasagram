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

@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        actor = instance.user

        if actor != post.user:
            threshold = timezone.now() - timedelta(minutes=5)
            
            existing_notif = Notification.objects.filter(
                user=post.user,
                actor=actor,
                post=post,
                type="post",
                created_at__gte=threshold
            ).first()

            if not existing_notif:
                # Створюємо нове, якщо старого немає
                Notification.objects.create(
                    user=post.user,
                    actor=actor,
                    post=post,
                    type="post"
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
                post=post,
                comment=instance,
                type="comment"
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
                chat=chat,
                type="chat"
            )

@receiver(post_save, sender=Notification)
def notify_on_new_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        # Рахуємо актуальну кількість
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
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from notifications.models import Notification


@receiver(post_save, sender=Message)
def send_message_notification(sender, instance, created, **kwargs):
    if created:
        chat = instance.chat
        actor = instance.user

        if actor != instance.user:
            Notification.objects.create(
                user=instance.user,
                actor=actor,
                chat=chat,
                type="chat"
            )
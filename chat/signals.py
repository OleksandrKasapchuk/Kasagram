from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from notifications.models import Notification


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
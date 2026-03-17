from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Like, Comment
from notifications.models import Notification


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        actor = instance.user

        if actor != post.user:
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


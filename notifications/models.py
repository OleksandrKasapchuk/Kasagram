from django.db import models
from auth_system.models import CustomUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Notification(models.Model):
    # Набір типів сповіщень для уникнення помилок
    class NotificationType(models.TextChoices):
        LIKE = 'LIKE', 'liked your post'
        COMMENT = 'COMMENT', 'commented on your post'
        MESSAGE = 'MESSAGE', 'sent you a message'
        FOLLOW = 'FOLLOW', 'started following you'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="actions")

    # Тип сповіщення, який легко читати фронтенду
    notification_type = models.CharField(
        max_length=20, 
        choices=NotificationType.choices,
        default=NotificationType.LIKE
    )

    # Generic Relation поля
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.actor} -> {self.user} ({self.notification_type})"
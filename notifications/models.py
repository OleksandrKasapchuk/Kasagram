from django.db import models
from auth_system.models import CustomUser
from post_system.models import *
from chat.models import *
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="actions")

    # Службові поля для Generic Relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    # Це і є наш "універсальний" об'єкт (Post, Comment, Chat тощо)
    target = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.actor} -> {self.user} ({self.type})"
    
    def get_url(self):
        # Тепер ми можемо просто викликати get_absolute_url у об'єкта, якщо він є
        if hasattr(self.target, 'get_absolute_url'):
            return self.target.get_absolute_url()
        return "#"

    def get_message(self):
        # Можна зробити словник типів для зручності
        messages = {
            'post': "liked your post",
            'comment': "commented on your post",
            'chat': "sent you a message",
        }
        # content_type.model поверне рядок 'post', 'comment' і т.д.
        return messages.get(self.content_type.model, "interacted with you")
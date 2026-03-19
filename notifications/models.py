# models.py
from django.db import models
from auth_system.models import CustomUser
from post_system.models import *
from chat.models import *
from django.urls import reverse

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('chat', 'Chat'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(CustomUser,on_delete=models.CASCADE, related_name="actions")

    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.actor} -> {self.user} ({self.type})"

    def get_url(self):
        if self.type == "post" and self.post:
            return reverse("post:post-details", args=[self.post.pk])

        if self.type == "chat" and self.chat:
            return reverse("chat:chat_detail", args=[self.chat.pk])

        if self.type == "comment" and self.comment:
            return reverse("post:post-details", args=[self.comment.post.pk])
        return "#"
    
    def get_message(self):
        if self.type == "post":
            return " liked your post"

        if self.type == "comment":
            return " commented on your post"

        if self.type == "chat":
            return " sent you a message"
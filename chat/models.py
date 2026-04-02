from django.db import models
from auth_system.models import CustomUser
from django.db.models import Max
from django.urls import reverse


class ChatManager(models.Manager):
    def for_user_sorted(self, user):
        return self.filter(participants=user).annotate(
            last_msg_date=Max('messages__timestamp')
        ).order_by('-last_msg_date')
    

class Chat(models.Model):
    participants = models.ManyToManyField(CustomUser, related_name='chats')
    created = models.DateTimeField(auto_now_add=True)
    objects = ChatManager()
    
    def __str__(self):
        return f"Chat between {', '.join([str(p) for p in self.participants.all()])}"
    
    def get_absolute_url(self):
        return reverse("chat:chat_detail", args=[self.pk])


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent = models.ForeignKey("self", models.SET_NULL, null=True, blank=True, related_name="replies")

    class Meta:
        ordering = ['timestamp', 'pk']
    def __str__(self):
        username = self.user.username
        time_str = self.timestamp.strftime("%H:%M")
        return f"[{time_str}] {username}"
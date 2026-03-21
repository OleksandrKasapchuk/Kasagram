from django.db import models
from auth_system.models import CustomUser


class Chat(models.Model):
    participants = models.ManyToManyField(CustomUser, related_name='chats')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat between {', '.join([str(p) for p in self.participants.all()])}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Message from {self.sender} at {self.timestamp}"
    

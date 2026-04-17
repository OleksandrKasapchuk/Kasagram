from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from django.utils import timezone


class CustomUser(AbstractUser):
    bio = models.TextField(null=True, blank=True)
    avatar = CloudinaryField("image")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return self.username
    

class Subscription(models.Model):
    follower = models.ForeignKey(CustomUser, related_name='following',on_delete=models.CASCADE)
    following = models.ForeignKey(CustomUser,related_name='followers',on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower} follows {self.following}'
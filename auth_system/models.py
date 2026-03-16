from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField

class CustomUser(AbstractUser):
	bio = models.TextField(null=True, blank=True)
	avatar = CloudinaryField("image")

	def __str__(self):
		return self.username
    

class Subscription(models.Model):
    user_from = models.ForeignKey(CustomUser, related_name='following',on_delete=models.CASCADE)
    user_to = models.ForeignKey(CustomUser,related_name='followers',on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_from', 'user_to')

    def __str__(self):
        return f'{self.user_from} follows {self.user_to}'
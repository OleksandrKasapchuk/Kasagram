from django.db import models
from auth_system.models import *
from cloudinary.models import CloudinaryField


class Post(models.Model):
	content = models.TextField(blank=True,null=True)
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="posts")
	media = CloudinaryField(resource_type="auto")
	date_published = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.user} - {self.date_published}"

	class Meta:
		ordering = ('-date_published',)


class Comment(models.Model):
	content = models.CharField(max_length=100)
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="comments")
	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
	date_published = models.DateTimeField(auto_now_add=True)
	parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies")
	
	def __str__(self):
		return f"{self.user} - {self.date_published}"
	
	class Meta:
		ordering = ('-date_published',)


class Like(models.Model):
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="likes")
	post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

	class Meta:
		unique_together = ('user', 'post')

	def __str__(self):
		return f"{self.user} - {self.post}"
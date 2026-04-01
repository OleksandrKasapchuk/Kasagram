from rest_framework import serializers
from .models import *
from auth_system.serializers import UserSerializer


class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    media_url = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'user', 'content', 'media_url', 'media',
            'date_published', 'likes_count', 'comments_count', 'is_liked'
        ]
        extra_kwargs = {
            'media': {'write_only': True}
        }

    def get_media_url(self, obj):
        if obj.media:
            return obj.media.url
        return None

    def get_is_liked(self, obj):
        # 1. Беремо request безпечно через .get()
        request = self.context.get('request')
        
        # 2. Перевіряємо, чи взагале є request і чи є в ньому юзер
        if request and request.user and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        
        # Якщо запиту немає (наприклад, при генерації профілю без передачі context)
        # або юзер не залогінений — повертаємо False
        return False

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'content', 'date_published', 'parent', 'replies_count']

    def get_replies_count(self, obj):
        return obj.replies.count()
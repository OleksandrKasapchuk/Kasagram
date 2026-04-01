from rest_framework import serializers
from .models import *
from auth_system.serializers import UserSerializer


class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    media_url = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'content', 'media_url', 'media',
            'date_published', 'likes_count', 'comments_count', 'is_liked', 'is_owner'
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
    
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'post', 'content', 
            'date_published', 'parent', 'replies_count', 'parent_id'
        ]
        read_only_fields = ['date_published', 'user']

    def get_replies_count(self, obj):
        return obj.replies.count()

    def create(self, validated_data):
        # Витягуємо parent_id, якщо він є
        parent_id = validated_data.pop('parent_id', None)
        if parent_id:
            validated_data['parent'] = Comment.objects.get(pk=parent_id)
        return super().create(validated_data)


class LikeActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['post'] # Нам треба знати тільки який пост лайкають

    def save(self, **kwargs):
        user = self.context['request'].user
        post = self.validated_data['post']
        
        like_qs = Like.objects.filter(post=post, user=user)
        
        if like_qs.exists():
            like_qs.delete()
            return None, False # Повертаємо (None об'єкт, False - не лайкнуто)
        else:
            new_like = Like.objects.create(post=post, user=user)
            return new_like, True # Повертаємо (Об'єкт лайка, True - лайкнуто)
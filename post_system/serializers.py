from rest_framework import serializers
from .models import *
from users.serializers import UserBaseSerializer


class PostBaseSerializer(serializers.ModelSerializer):
    media_url = serializers.ReadOnlyField(source='media.url')
    
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'media_url', 'likes_count', 'comments_count'
        ]


class PostSerializer(PostBaseSerializer):
    user = UserBaseSerializer(read_only=True)
    
    is_liked = serializers.BooleanField(read_only=True)
    is_owner = serializers.BooleanField(read_only=True)
    
    class Meta(PostBaseSerializer.Meta):
        fields = PostBaseSerializer.Meta.fields + [
            'user', 'content', 'media', 'date_published', 'is_liked', 'is_owner'
        ]
        extra_kwargs = {
            'media': {'write_only': True}
        }


class PostDetailSerializer(PostSerializer):
    # Додаємо список коментарів
    comments = serializers.SerializerMethodField()

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ['comments']

    def get_comments(self, obj):
        # Беремо тільки "батьківські" коментарі (parent=None)
        # Реплаї підтягнуться автоматично через CommentSerializer
        root_comments = obj.comments.filter(parent__isnull=True)
        return CommentSerializer(root_comments, many=True).data


class CommentSerializer(serializers.ModelSerializer):
    user = UserBaseSerializer(read_only=True)
    parent_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    # Додаємо replies для відображення дерева (Read Only)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'post', 'content', 
            'date_published', 'parent', 'parent_id', 'replies'
        ]
        read_only_fields = ['date_published', 'user']

    def get_replies(self, obj):
        # Якщо у коментаря є реплаї, серіалізуємо їх цим же серіалізатором
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

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
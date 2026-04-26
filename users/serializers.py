from rest_framework import serializers
from auth_system.models import CustomUser, Subscription
from django.db.models import Count

class RegisterSerializer(serializers.ModelSerializer):
    # Пароль тільки для запису, ми не хочемо повертать його в JSON
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'email', 'first_name', 'last_name', 'bio']

    def create(self, validated_data):
        # Використовуємо спеціальний метод моделі для створення юзера з хешованим паролем
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            bio=validated_data.get('bio', '')
        )
        return user


# 1. Тільки те, що треба скрізь
class UserBaseSerializer(serializers.ModelSerializer):
    avatar_url = serializers.ReadOnlyField(source='avatar.url')
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'avatar_url']


# 2. Публічна інфа (ідеально підходить для ЧАТУ та списків)
class UserPublicSerializer(UserBaseSerializer):
    is_following = serializers.BooleanField(source='is_following_annotated', read_only=True)
    
    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + ['is_online', 'last_seen', 'is_following']


class UserDetailSerializer(UserPublicSerializer):
    posts = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField(read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
    followings_count = serializers.IntegerField(read_only=True)


    class Meta(UserPublicSerializer.Meta):
        model = CustomUser
        # Додаємо нові поля до вже існуючих
        fields = UserPublicSerializer.Meta.fields + [
            'first_name', 'last_name', 'is_online', 
            'last_seen', 'bio', 'posts', 'posts_count', 
            'followers_count', 'followings_count', 'is_following'
        ]
    
    def get_posts(self, obj):
        from post_system.serializers import PostBaseSerializer

        posts = obj.posts.annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True)
        ).order_by('-date_published')[:12]
        return PostBaseSerializer(posts, many=True).data



class SubscriptionSerializer(serializers.ModelSerializer):
    
    follower_details = UserBaseSerializer(source='follower', read_only=True)
    following_details = UserBaseSerializer(source='following', read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'follower', 'following', 'follower_details', 'following_details', 'created']
        read_only_fields = ['created']

    def validate(self, data):
        # Перевірка: не можна підписатися на самого себе
        if data['follower'] == data['following']:
            raise serializers.ValidationError("You cannot follow yourself.")
        return data
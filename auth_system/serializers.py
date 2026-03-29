from rest_framework import serializers
from .models import CustomUser, Subscription



class UserDetailSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    # Включаємо список постів через інший серіалізатор
    def get_user_posts(self, obj):
        from post_system.serializers import PostSerializer # Імпорт всередині!
        posts = obj.posts.all() # або obj.posts.all()
        return PostSerializer(posts, many=True).data

    user_posts = serializers.SerializerMethodField()
    
    # Можна додати додаткові поля, яких немає в базовому
    posts_count = serializers.IntegerField(source='post_set.count', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar_url', 'is_online', 'last_seen', 'bio','user_posts', 'posts_count']

    def get_avatar_url(self, obj):
        if obj.avatar:
            # Повертаємо пряме посилання на картинку в Cloudinary
            return obj.avatar.url
        # Можна повернути дефолтну картинку, якщо аватара немає
        return "https://res.cloudinary.com/your_cloud_name/image/upload/v1/default_avatar.jpg"


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'avatar_url'] # Тільки база

    def get_avatar_url(self, obj):
        if obj.avatar:
            # Повертаємо пряме посилання на картинку в Cloudinary
            return obj.avatar.url
        # Можна повернути дефолтну картинку, якщо аватара немає
        return "https://res.cloudinary.com/your_cloud_name/image/upload/v1/default_avatar.jpg"


class SubscriptionSerializer(serializers.ModelSerializer):
    # Використовуємо наш UserSerializer, щоб бачити деталі юзера, а не просто ID
    user_from_details = UserSerializer(source='user_from', read_only=True)
    user_to_details = UserSerializer(source='user_to', read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'user_from', 'user_to', 'user_from_details', 'user_to_details', 'created']
        read_only_fields = ['created']

    def validate(self, data):
        # Перевірка: не можна підписатися на самого себе
        if data['user_from'] == data['user_to']:
            raise serializers.ValidationError("You cannot follow yourself.")
        return data
from rest_framework import serializers
from auth_system.models import CustomUser, Subscription


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


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'avatar_url', 'is_following']

    def get_avatar_url(self, obj):
        if obj.avatar:
            # Повертаємо пряме посилання на картинку в Cloudinary
            return obj.avatar.url
        return None
    
    def get_is_following(self, obj):
        # Отримуємо об'єкт запиту з контексту серіалізатора
        request = self.context.get('request')
        
        # Якщо користувач не авторизований або запиту немає — повертаємо False
        if not request or not request.user.is_authenticated:
            return False
        
        # Важливо: користувач не може бути підписаним на самого себе (логічно)
        if request.user == obj:
            return False

        # Перевіряємо наявність запису в моделі Subscription
        # Припускаємо, що у тебе поля називаються 'follower' та 'following'
        return Subscription.objects.filter(
            follower=request.user, 
            following=obj
        ).exists()


class UserDetailSerializer(UserSerializer):
    posts = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField(source='posts.count', read_only=True)

    followers_count = serializers.IntegerField(source='followers.count', read_only=True)
    followings_count = serializers.IntegerField(source='following.count', read_only=True)


    class Meta(UserSerializer.Meta):
        model = CustomUser
        # Додаємо нові поля до вже існуючих
        fields = UserSerializer.Meta.fields + [
            'first_name', 'last_name', 'is_online', 
            'last_seen', 'bio', 'posts', 'posts_count', 
            'followers_count', 'followings_count', 'is_following'
        ]
    
    def get_posts(self, obj):
        from post_system.serializers import PostSerializer
        return PostSerializer(obj.posts.all(), many=True).data


class SubscriptionSerializer(serializers.ModelSerializer):
    # Використовуємо наш UserSerializer, щоб бачити деталі юзера, а не просто ID
    follower_details = UserSerializer(source='follower', read_only=True)
    following_details = UserSerializer(source='following', read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'follower', 'following', 'follower_details', 'following_details', 'created']
        read_only_fields = ['created']

    def validate(self, data):
        # Перевірка: не можна підписатися на самого себе
        if data['follower'] == data['following']:
            raise serializers.ValidationError("You cannot follow yourself.")
        return data
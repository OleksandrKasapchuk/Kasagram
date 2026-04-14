from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import CustomUser, Subscription
from django.shortcuts import  get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from .serializers import *


# 1. ДЛЯ ТИХ ХТО ВЖЕ МАЄ АККАУНТ (ЛОГІН)
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # Ця штука всередині сама перевірить username та password
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username
        })

# 2. ДЛЯ НОВИХ (РЕЄСТРАЦІЯ) - те що ми писали раніше
@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    # 1. Віддаємо дані серіалізатору
    serializer = RegisterSerializer(data=request.data)
    
    # 2. Валідація! Якщо юзернейм вже є — DRF сам видасть помилку 400
    if serializer.is_valid():
        user = serializer.save() # Це викличе метод create() в серіалізаторі
        
        # 3. Створюємо токен для нового юзера
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key, 
            'user_id': user.id,
            'username': user.username
        }, status=201) # 201 Created — правильний статус для реєстрації
    
    # Якщо дані "криві" — повертаємо помилки (наприклад: "цей email вже зайнятий")
    return Response(serializer.errors, status=400)


class UserDetailAPIView(APIView):
    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        
        # Перетворюємо об'єкт юзера в JSON
        serializer = UserDetailSerializer(user)
        
        return Response(serializer.data)


class ToggleFollowAPIView(APIView):
    def post(self, request, pk):
        user_to = get_object_or_404(CustomUser, pk=pk)
        
        # Перевірка на підписку на самого себе
        if request.user == user_to:
            return Response(
                {'error': 'You cannot follow yourself.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription_qs = Subscription.objects.filter(
            user_from=request.user, 
            user_to=user_to
        )

        if subscription_qs.exists():
            subscription_qs.delete()
            following = False
        else:
            Subscription.objects.create(user_from=request.user, user_to=user_to)
            following = True
        
        return Response({
            'following': following,
            'followers_count': user_to.followers.count(),
            'following_count': user_to.following.count(),
        }, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
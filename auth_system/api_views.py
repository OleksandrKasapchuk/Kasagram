from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import CustomUser
from rest_framework.permissions import IsAuthenticated
from .serializers import UserDetailSerializer
from django.shortcuts import  get_object_or_404


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
    username = request.data.get('username')
    password = request.data.get('password')
    
    # Створюємо юзера (якщо його нема)
    user = CustomUser.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    
    return Response({
        'token': token.key, 
        'user_id': user.id
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Тільки залогінені бачать профілі
def get_user_detail(request, id):
    # Шукаємо юзера за ID, який прийшов з Android
    user = get_object_or_404(CustomUser, pk=id)
    
    # Перетворюємо об'єкт юзера в JSON
    serializer = UserDetailSerializer(user)
    
    return Response(serializer.data)
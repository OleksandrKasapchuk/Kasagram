from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import CustomUser
from rest_framework.permissions import IsAuthenticated
from .serializers import *
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

@api_view(['GET'])
@permission_classes([IsAuthenticated]) # Тільки залогінені бачать профілі
def get_user_detail(request, id):
    # Шукаємо юзера за ID, який прийшов з Android
    user = get_object_or_404(CustomUser, pk=id)
    
    # Перетворюємо об'єкт юзера в JSON
    serializer = UserDetailSerializer(user)
    
    return Response(serializer.data)
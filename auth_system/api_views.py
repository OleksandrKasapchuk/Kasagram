from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from users.serializers import *


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


# 3. ЗМІНА ПАРОЛЯ - для авторизованих користувачів
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_change_password(request):
    """
    Endpoint для зміни пароля авторизованого користувача
    Вимагає: old_password, new_password, new_password_confirm
    """
    user = request.user
    serializer = ChangePasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        # Перевіряємо що старий пароль правильний
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': 'Старий пароль невірний.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Встановлюємо новий пароль
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response(
            {'detail': 'Пароль успішно змінено.'},
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 4. РЕДАГУВАННЯ ПРОФІЛЮ - для авторизованих користувачів
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def api_edit_profile(request):
    """
    Endpoint для редагування профілю авторизованого користувача
    Можна редагувати: email, first_name, last_name, bio, avatar
    """
    user = request.user
    serializer = EditProfileSerializer(user, data=request.data, partial=True, context={'request': request})
    
    if serializer.is_valid():
        serializer.save()
        
        return Response(
            {
                'detail': 'Профіль успішно оновлено.',
                'user': UserDetailSerializer(user, context={'request': request}).data
            },
            status=status.HTTP_200_OK
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
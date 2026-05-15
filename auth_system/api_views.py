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

# # 2. ДЛЯ НОВИХ (РЕЄСТРАЦІЯ) - те що ми писали раніше
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def api_register(request):
#     # 1. Віддаємо дані серіалізатору
#     serializer = RegisterSerializer(data=request.data)
    
#     # 2. Валідація! Якщо юзернейм вже є — DRF сам видасть помилку 400
#     if serializer.is_valid():
#         user = serializer.save() # Це викличе метод create() в серіалізаторі
        
#         # 3. Створюємо токен для нового юзера
#         token, _ = Token.objects.get_or_create(user=user)
        
#         return Response({
#             'token': token.key, 
#             'user_id': user.id,
#             'username': user.username
#         }, status=201) # 201 Created — правильний статус для реєстрації
    
#     # Якщо дані "криві" — повертаємо помилки (наприклад: "цей email вже зайнятий")
#     return Response(serializer.errors, status=400)

from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
import random
import logging
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

logger = logging.getLogger(__name__)


class APIStartRegistrationView(APIView):
    permission_classes = [AllowAny]
    
    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data
            # Оскільки ми ще не створюємо юзера, пароль треба зберегти захешованим 
            # або передати як є, якщо довіряєте сесії
            verification_code = str(random.randint(100000, 999999))
            
            # Зберігаємо дані в сесію
            request.session['registration_data'] = user_data
            request.session['verification_code'] = verification_code
            # Важливо для API: примусово зберігаємо сесію
            request.session.modified = True 

            try:
                send_mail(
                    subject='Verifizierung der Registrierung',
                    message=f'Ihr Code: {verification_code}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user_data['email']],
                    fail_silently=False,
                )
                return Response({
                    "message": "Код відправлено на пошту"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Mail sending failed: {e}")
                return Response({
                    "error": "Помилка відправки пошти"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.authtoken.models import Token

class APIVerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_code = request.data.get('code')
        session_code = request.session.get('verification_code')
        reg_data = request.session.get('registration_data')

        if not reg_data or not session_code:
            return Response({"error": "Сесія реєстрації застаріла або відсутня"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        if user_code == session_code:
            # Створюємо юзера (використовуємо метод моделі або серіалізатора)
            # Врахуйте, що RegisterSerializer.save() зазвичай створює об'єкт
            # Тому краще викликати створення через менеджер:
            try:
                user = CustomUser.objects.create_user(
                    email=reg_data['email'],
                    username=reg_data.get('username', reg_data['email']), # Якщо username обов'язковий
                    first_name=reg_data.get('first_name', ''),
                    last_name=reg_data.get('last_name', ''),
                    password=reg_data['password']
                )
                
                # Створюємо токен
                token, _ = Token.objects.get_or_create(user=user)

                # Очищуємо сесію
                del request.session['verification_code']
                del request.session['registration_data']

                return Response({
                    'token': token.key,
                    'user_id': user.id,
                    'username': user.username
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error": "Невірний код!"}, status=status.HTTP_400_BAD_REQUEST)


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
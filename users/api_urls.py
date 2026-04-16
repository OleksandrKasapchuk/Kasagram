from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .api_views import *


# 1. Створюємо рутер для ViewSet
router = DefaultRouter()
# Реєструємо наш ViewSet. Це створить шляхи:
# /users/{pk}/ 
# /users/{pk}/followers/
# /users/{pk}/following/
router.register(r'users', UserRelationshipViewSet, basename='user')

urlpatterns = [
    # 2. Твої існуючі APIView
    path('me/', MeAPIView.as_view(), name='api_me'),
    path('toggle-follow/<int:pk>/', ToggleFollowAPIView.as_view(), name='api_toggle_follow'),
    # 3. Підключаємо всі автоматичні шляхи рутера
    path('', include(router.urls)),
]
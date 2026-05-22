from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .api_views import PostViewSet, CommentViewSet, LikeAPIView, PingView

# Ініціалізуємо чистий SimpleRouter
router = SimpleRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    # Системні та кастомні ендпоінти
    path('ping/', PingView.as_view(), name="ping"),
    path('like/<int:pk>/', LikeAPIView.as_view(), name="post-like"),

    # Автоматичні маршрути для постів та коментарів
    path('', include(router.urls)),
]
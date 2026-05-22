from django.urls import path, include
from .api_views import *
from rest_framework.routers import SimpleRouter


router = SimpleRouter()
router.register(r'comments', CommentViewSet, basename='comment')


urlpatterns = [
    path('ping/', PingView.as_view(), name="ping"),
    path('posts/', PostListAPIView.as_view()),
    path('posts/<int:pk>/', PostDetailAPIView.as_view()),
    path('posts/create/', PostCreateAPIView.as_view()),
    path('like/<int:pk>/', LikeAPIView.as_view()),
    path('', include(router.urls)),
]
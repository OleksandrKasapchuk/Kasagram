from django.urls import path
from post_system.api_views import *


urlpatterns = [
    path('ping/', PingView.as_view(), name="ping"),
    path('posts/', PostListAPIView.as_view()),
    path('posts/create/', PostCreateAPIView.as_view()),
    path('like/<int:pk>/', LikeAPIView.as_view()),
    path('delete-comment/<int:pk>/', DeleteCommentAPIView.as_view(), name='delete-comment'),
]
from django.urls import path
from chat.api_views import ChatListAPIView, MessageListAPIView
from post_system.api_views import *
from rest_framework.authtoken import views as auth_views


urlpatterns = [
    path('chats/', ChatListAPIView.as_view()),
    path('messages/<int:chat_id>/', MessageListAPIView.as_view()),
]
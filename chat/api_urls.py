from django.urls import path
from chat.api_views import ChatListAPIView
from post_system.api_views import *
from .views import ChatMessagesView

urlpatterns = [
    path('chats/', ChatListAPIView.as_view()),
    path('messages/<int:pk>/', ChatMessagesView.as_view()),
]
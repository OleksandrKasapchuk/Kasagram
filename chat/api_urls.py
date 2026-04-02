from django.urls import path
from chat.api_views import *
from .views import *

urlpatterns = [
    path('chats/', ChatListAPIView.as_view()),
    path('messages/<int:pk>/', ChatMessagesAPIView.as_view(), name='get_messages'),
]

app_name = "chat_api"
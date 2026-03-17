from django.urls import path
from .views import *


urlpatterns = [
    path('',ChatListView.as_view(), name='chat_list'),
    path('<int:pk>/',ChatDetailView.as_view(), name='chat_detail'),
    path('messages/<int:pk>/', ChatMessagesView.as_view(), name='get_messages'),
    path('start/<int:pk>/', start_chat, name='start_chat'),
	path('delete-message/<int:pk>', DeleteMessageView.as_view(), name='delete_message'),
]

app_name = "chat"
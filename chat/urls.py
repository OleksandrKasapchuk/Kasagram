from django.urls import path
from .views import *


urlpatterns = [
    path('',ChatListView.as_view(), name='chat_list'),
    path('<int:pk>/',ChatDetailView.as_view(), name='chat_detail'),
    path('start/<int:pk>/', start_chat, name='start_chat'),
]

app_name = "chat"
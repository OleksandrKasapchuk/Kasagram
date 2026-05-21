from .models import Chat
from .serializers import ChatSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from common.permissions import *
from django.shortcuts import get_object_or_404
from .mixins import ChatMessageMixin
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.response import Response
from users.serializers import UserPublicSerializer


class ChatPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ChatListAPIView(ListAPIView):
    serializer_class = ChatSerializer
    pagination_class = ChatPagination

    def get_queryset(self):
        return Chat.objects.for_user_sorted(self.request.user)


class ChatMessagesAPIView(APIView, ChatMessageMixin):
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        if not chat.participants.filter(id=request.user.id).exists():
            return Response({'success': False, 'error': 'Unauthorized'}, status=403)
        
        participant = UserPublicSerializer(chat.participants.exclude(id=request.user.pk).first()).data

        oldest_id = request.GET.get('oldest_id') 
        messages_data = self.get_serialized_messages(chat, request, oldest_id=oldest_id)
            
        return Response({
            'success': True, 
            'messages': messages_data,
            'participant': participant
        })
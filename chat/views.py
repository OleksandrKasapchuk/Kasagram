from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from auth_system.models import CustomUser
from .models import Chat, Message
from post_system.mixins import *
from .mixins import ChatMessageMixin
from .serializers import ChatSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.response import Response
from auth_system.serializers import UserSerializer


class ChatListView(LoginRequiredMixin, ListView):
    model = Chat
    template_name = 'chat/chat_list.html'
    context_object_name = 'chats'

    def get_queryset(self):
        return self.request.user.chats.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        serializer = ChatSerializer(context['chats'], many=True, context={'request': self.request})
        
        chat_data = serializer.data

        chat_data.sort(
            key=lambda x: x['last_message']['timestamp'] if x['last_message'] else '', 
            reverse=True
        )
        
        context['chat_list_data'] = chat_data
        return context


class ChatDetailView(LoginRequiredMixin, ChatMessageMixin , View):
    def get(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        if request.user not in chat.participants.all():
            return redirect('chat:chat_list')

        participant = chat.participants.exclude(id=request.user.pk).first()
        
        messages_data = self.get_serialized_messages(chat, request)
        
        context = {
            'chat': chat,
            'participant': participant,
            'messages': messages_data
        }
        return render(request, 'chat/chat_detail.html', context)


class ChatMessagesView(APIView, ChatMessageMixin):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        if not chat.participants.filter(id=request.user.id).exists():
            return Response({'success': False, 'error': 'Unauthorized'}, status=403)
        
        participant = UserSerializer(chat.participants.exclude(id=request.user.pk).first()).data

        oldest_id = request.GET.get('oldest_id') 
        messages_data = self.get_serialized_messages(chat, request, oldest_id=oldest_id)
            
        return Response({
            'success': True, 
            'messages': messages_data,
            'participant': participant
        })


@login_required
def start_chat(request, pk):
    user_to_chat = get_object_or_404(CustomUser, pk=pk)
    chat = Chat.objects.filter(participants=request.user).filter(participants=user_to_chat).first()
    
    if chat:
        return redirect('chat:chat_detail', pk=chat.pk)
    else:
        new_chat = Chat.objects.create()
        new_chat.participants.add(request.user, user_to_chat)
        return redirect('chat:chat_detail', pk=new_chat.pk)


class DeleteMessageView(LoginRequiredMixin, View):
    def delete(self, request, pk, *args, **kwargs):
        message = get_object_or_404(Message, pk=pk)
        if request.user == message.user:
            message.delete()
            return JsonResponse({'success': True, 'message': 'Message deleted successfully.'})
        else:
            return JsonResponse({'success': False, 'message': 'You do not have permission to delete this message.'}, status=403)
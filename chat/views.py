from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from auth_system.models import CustomUser
from .models import Chat
from post_system.mixins import *
from .mixins import ChatMessageMixin
from .serializers import ChatSerializer


class ChatListView(LoginRequiredMixin, ListView):
    model = Chat
    template_name = 'chat/chat_list.html'
    
    def get_queryset(self):
        # Повертаємо об'єкти, як того хоче Django
        return Chat.objects.for_user_sorted(self.request.user)

    def get_context_data(self, **kwargs):
        # Отримуємо базовий контекст
        context = super().get_context_data(**kwargs)
        
        # Беремо QuerySet, який повернув get_queryset
        queryset = self.get_queryset()
        
        # Серіалізуємо його точно так само, як в API
        serializer = ChatSerializer(
            queryset, 
            many=True, 
            context={'request': self.request} # Важливо для посилань на фото/файли
        )
        
        # Передаємо в шаблон вже готові дані
        context['chat_list_data'] = serializer.data
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


@login_required
def start_chat(request, pk):
    following_chat = get_object_or_404(CustomUser, pk=pk)
    chat = Chat.objects.filter(participants=request.user).filter(participants=following_chat).first()
    
    if chat:
        return redirect('chat:chat_detail', pk=chat.pk)
    else:
        new_chat = Chat.objects.create()
        new_chat.participants.add(request.user, following_chat)
        return redirect('chat:chat_detail', pk=new_chat.pk)
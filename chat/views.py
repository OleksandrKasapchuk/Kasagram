from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from auth_system.models import CustomUser
from .models import Chat, Message
from post_system.mixins import *
from .mixins import ChatMessageMixin


class ChatListView(LoginRequiredMixin, ListView):
    model = Chat
    template_name = 'chat/chat_list.html'
    context_object_name = 'chats'

    def get_queryset(self):
        return self.request.user.chats.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat_data = []
        for chat in context['chats']:
            participant = chat.participants.exclude(id=self.request.user.id).first()
            # Беремо останнє повідомлення
            last_message = chat.messages.order_by('-timestamp').first()
            unread_count = chat.messages.filter(user=participant, is_read=False).count()
            chat_data.append({
                'chat': chat,
                'participant': participant,
                'last_message': last_message,
                'unread_count': unread_count,
            })
        
        # Сортуємо самі чати так, щоб ті, де свіжіші повідомлення, були зверху
        chat_data.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else chat.id, reverse=True)
        
        context['chat_list_data'] = chat_data
        return context


class ChatDetailView(LoginRequiredMixin, ChatMessageMixin , View):
    def get(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        if request.user not in chat.participants.all():
            return redirect('chat:chat_list')

        participant = chat.participants.exclude(id=request.user.pk).first()
        
        messages_data = self.get_serialized_messages(chat, request)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'messages': messages_data})

        context = {
            'chat': chat,
            'participant': participant,
            'messages': messages_data # Тепер тут вже готові словники, а не QuerySet
        }
        return render(request, 'chat/chat_detail.html', context)

    def post(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        if request.user not in chat.participants.all():
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

        content = request.POST.get('content')
        if not content:
            return JsonResponse({'success': False, 'error': 'No content provided'}, status=400)

        try:
            message = Message.objects.create(
                chat=chat,
                user=request.user,
                content=content
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'username': request.user.username,
                    'content': message.content,
                })
            return redirect('chat:chat_detail', pk=chat.pk)
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            raise e


class ChatMessagesView(LoginRequiredMixin, ChatMessageMixin, View):
    def get(self, request, pk):
        chat = get_object_or_404(Chat, id=pk)
        if request.user not in chat.participants.all():
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
        oldest_id = request.GET.get('oldest_id') 
        messages_data = self.get_serialized_messages(chat, request, oldest_id=oldest_id)
            
        return JsonResponse({
            'success': True, 
            'messages': messages_data
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
from django.shortcuts import  get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from chat.models import *
from .models import *
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from .models import CustomUser
from .forms import MyRegisterForm, UserEditForm



class RegisterView(CreateView):
    form_class = MyRegisterForm
    template_name = "form.html"
    success_url = '/'

    def form_valid(self, form):
        valid = super().form_valid(form)
        login(self.request, self.object)
        return valid


# Профіль користувача
class UserDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'auth_system/user_info.html'
    context_object_name = 'user'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_user = self.get_object()
        
        # Перевіряємо, чи підписаний поточний юзер на цей профіль
        # (assuming Subscription model has user_from and user_to)
        is_following = Subscription.objects.filter(
            user_from=self.request.user, 
            user_to=target_user
        ).exists()
        
        context['is_following'] = is_following
        return context

# Редагування профілю
class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserEditForm
    template_name = "form.html"

    def get_object(self):
        return self.request.user # Редагуємо тільки себе

    def get_success_url(self):
        return f"/user-info/{self.request.user.id}/"


@login_required
def toggle_follow(request, pk):
    user_to = get_object_or_404(CustomUser, id=pk)
    # Унеможливлюємо підписку на самого себе
    if request.user == user_to:
        return JsonResponse({'error': 'You cannot follow yourself.'}, status=400)

    subscription = Subscription.objects.filter(user_from=request.user,user_to=user_to)

    if subscription.exists():
        subscription.delete()
        following = False
    else:
        Subscription.objects.create(user_from=request.user,user_to=user_to)
        following = True
    
    return JsonResponse({
        'following': following,
        'followers_count': user_to.followers.count(),
        'following_count': user_to.following.count(),
    })

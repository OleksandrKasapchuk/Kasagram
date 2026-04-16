from chat.models import *
from auth_system.models import *
from django.views.generic import UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserEditForm


# Профіль користувача
class UserDetailView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'users/user_info.html'
    context_object_name = 'user'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_user = self.get_object()
        
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



class FollowerView(ListView):
	model = CustomUser
	template_name = 'users/user_list.html'

	def get_queryset(self):
		user = CustomUser.objects.get(pk=self.kwargs['pk'])
		return user.followers.all().values_list('user_from', flat=True)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['type'] = "Follower"
		context['users'] = CustomUser.objects.filter(pk__in=self.get_queryset())
		context["following"] = CustomUser.objects.get(pk=self.kwargs['pk']).following.values_list('user_to_id', flat=True)
		return context


class FollowingView(ListView):
	model = CustomUser
	template_name = 'users/user_list.html'
	
	def get_queryset(self):
		user = CustomUser.objects.get(pk=self.kwargs['pk'])
		return user.following.all().values_list('user_to', flat=True)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['type'] = "Following"
		context['users'] = CustomUser.objects.filter(pk__in=self.get_queryset())
		context["following"] = CustomUser.objects.get(pk=self.kwargs['pk']).following.values_list('user_to_id', flat=True)
		return context

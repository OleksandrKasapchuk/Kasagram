from django.shortcuts import redirect, get_object_or_404
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.views.generic import View, ListView, DetailView, UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from .serializers import *
from .mixins import *
from .forms import *
from .models import *


class Index(ListView):
	model = Post
	context_object_name = "posts"
	paginate_by = 3  # Обмеження на кількість постів на сторінці
	def get_template_names(self):
		if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
			return ["post_system/post_list.html"]  # Окремий шаблон для шматка постів
		return ["post_system/index.html"]

	def get_queryset(self):
		# Отримуємо категорію з параметрів запиту
		category = self.request.GET.get('category', 'for_you')

		# Фільтрація на основі категорії
		if category == 'following' and self.request.user.is_authenticated:
			# Отримуємо підписки користувача
			following_users = Subscription.objects.filter(user_from=self.request.user).values_list('user_to', flat=True)
			return Post.objects.filter(user__in=following_users).order_by('-date_published')
		else:
			return  Post.objects.all().order_by('-date_published')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		category = self.request.GET.get('category', 'for_you')
		context['category'] = category
		return context


class PostDetailView(DetailView):
	model = Post
	context_object_name ='post'
	template_name = 'post_system/post_details.html'

	def post(self, request,pk, *args, **kwargs):
		post = get_object_or_404(Post, pk=pk)
		content = request.POST.get('content')
		parent_id = request.POST.get('parent_id')
		try:
			comment = Comment.objects.create(
			post=post,
			user=request.user,
			content=content,
			parent_id=parent_id
			)
			readable_time = str(naturaltime(comment.date_published))
			if request.headers.get('x-requested-with') == 'XMLHttpRequest':
				return JsonResponse({
					'success': True,
					'username': request.user.username,
					'content': comment.content,
					'avatar_url': request.user.avatar.url,
					'date_published': readable_time,
					'user_url': reverse_lazy('user-info', kwargs={"pk":comment.user.pk}),
					'update_url': reverse_lazy('post:update-comment', kwargs={"pk":comment.pk}),
					'commentId': comment.pk,
				})
			return redirect('post:post_details', pk=post.pk)
		except Exception as e:
			if request.headers.get('x-requested-with') == 'XMLHttpRequest':
				return JsonResponse({'success': False, 'error': str(e)})
			raise e


class PostCreateView(LoginRequiredMixin, CreateView):
	model = Post
	form_class = PostCreateForm
	template_name = "form.html"
	success_url = reverse_lazy("post:index")

	def form_valid(self, form):
		form.instance.user = self.request.user  # Прив'язуємо юзера автоматично
		return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserIsOwnerMixin, UpdateView):
	model = Post
	form_class = PostCreateForm
	template_name = "form.html"
	success_url = reverse_lazy("post:index")

	def form_valid(self, form):
		# Якщо треба щось додати перед збереженням
		return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, UserIsOwnerMixin, DeleteView):
	model = Post
	template_name = "form.html"

	def get_success_url(self) -> str:
		return reverse_lazy("post:index")


class LikeView(View):
	def post(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=403)
		
		post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
		like_qs = Like.objects.filter(post=post, user=request.user)
		
		if like_qs.exists():
			like_qs.delete()
			liked = False
		else:
			like = Like.objects.create(post=post, user=request.user)
			liked = True
		data = {
			'liked': liked,
			'likes_count': post.likes.count()
		}
		return JsonResponse(data)


class DeleteCommentView(LoginRequiredMixin, View):
	def post(self, request, *args, **kwargs):
		pk = self.kwargs.get('pk')
		comment = get_object_or_404(Comment, pk=pk)
		if request.user == comment.user:
			comment.delete()
			return JsonResponse({'success': True, 'message': 'Comment deleted successfully.'})
		else:
			return JsonResponse({'success': False, 'message': 'You do not have permission to delete this comment.'}, status=403)


class UpdateCommentView(LoginRequiredMixin,UserIsOwnerMixin,UpdateView):
	model = Comment
	template_name = "form.html"
	context_object_name = "comment"
	form_class = CommentCreateForm

	def get_success_url(self) -> str:
		return reverse_lazy("post:post-details", kwargs={'pk': self.object.post.pk})


class FollowerView(ListView):
	model = CustomUser
	template_name = 'post_system/user_list.html'

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
	template_name = 'post_system/user_list.html'
	
	def get_queryset(self):
		user = CustomUser.objects.get(pk=self.kwargs['pk'])
		return user.following.all().values_list('user_to', flat=True)
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['type'] = "Following"
		context['users'] = CustomUser.objects.filter(pk__in=self.get_queryset())
		context["following"] = CustomUser.objects.get(pk=self.kwargs['pk']).following.values_list('user_to_id', flat=True)
		return context

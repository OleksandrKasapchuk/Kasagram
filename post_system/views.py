from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .models import *
from notifications.models import Notification
from django.views.generic import View, ListView, DetailView, CreateView, TemplateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .mixins import *
from .forms import *


from django.core.paginator import Paginator

class Index(ListView):
    model = Post
    context_object_name = "posts"
    template_name = "post_system/index.html"
    paginate_by = 3  # Обмеження на кількість постів на сторінці

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
		try:
			comment = Comment.objects.create(
			post=post,
			user=request.user,
			content=content
			)
			if request.headers.get('x-requested-with') == 'XMLHttpRequest':
				return JsonResponse({
					'success': True,
					'username': request.user.username,
					'content': comment.content,
					'avatar_url': request.user.avatar.url,
					'date_published': comment.date_published,
					'user_url': reverse_lazy('user-info', kwargs={"pk":comment.user.pk}),
					'update_url': reverse_lazy('post:update-comment', kwargs={"pk":comment.pk}),
					'delete_url': reverse_lazy('post:delete-comment', kwargs={"pk":comment.pk}),
				})
			return redirect('post:post_details', pk=post.pk)
		except Exception as e:
			if request.headers.get('x-requested-with') == 'XMLHttpRequest':
				return JsonResponse({'success': False, 'error': str(e)})
			raise e


class PostCreateView(LoginRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		return render(
			request,
			"form.html",
			context = {"form": PostCreateForm}
		)

	def post(self, request, *args, **kwargs):
		form = PostCreateForm(request.POST, request.FILES)
		if form.is_valid():
			post = form.save(commit=False)
			post.user = self.request.user
			post.save()
			return redirect("post:index")
		else:
			pass


class PostUpdateView(LoginRequiredMixin, UserIsOwnerMixin, UpdateView):
	model = Post
	def get(self, request, pk, *args, **kwargs):
		return render(
			request,
			"post_system/edit_post.html",
			context={"post": Post.objects.get(pk=pk)}
		)

	def post(self, request, pk, *args, **kwargs):
		post = Post.objects.get(pk=pk)
		post.content = request.POST.get('content')
		if request.FILES.get('media') != None:
			post.media = request.FILES.get('media')
		post.save()
		return redirect("post:index")


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
		return reverse_lazy("post:post-details")


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

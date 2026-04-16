from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .serializers import *
from .mixins import *
from .forms import *
from .models import *


class IndexView(PostQuerysetMixin, ListView):
    model = Post
    context_object_name = "posts"
    paginate_by = 3
    template_name = "post_system/index.html"

    def get_queryset(self):
        return self.get_post_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.request.GET.get('category', 'for_you')
        return context


class PostDetailView(DetailView):
	model = Post
	context_object_name ='post'
	template_name = 'post_system/post_details.html'


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


class UpdateCommentView(LoginRequiredMixin,UserIsOwnerMixin,UpdateView):
	model = Comment
	template_name = "form.html"
	context_object_name = "comment"
	form_class = CommentCreateForm

	def get_success_url(self) -> str:
		return reverse_lazy("post:post-details", kwargs={'pk': self.object.post.pk})
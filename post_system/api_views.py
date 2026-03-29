from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from .models import Post
from .serializers import PostSerializer
from rest_framework import generics
from auth_system.models import Subscription
from rest_framework.permissions import AllowAny 
from rest_framework.pagination import PageNumberPagination


class PostPagination(PageNumberPagination):
    page_size = 3  # Тільки для постів буде по 3
    page_size_query_param = 'page_size' # Дозволяє Android самому просити більше, якщо треба
    max_page_size = 100


class PingView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"status": "server works"})


class PostListAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PostSerializer
    pagination_class = PostPagination  # ОСЬ ТУТ МИ КАЖЕМО: "Пагінуй тільки це в'ю"

    def get_queryset(self):
        category = self.request.query_params.get('category', 'for_you')

        if category == 'following' and self.request.user.is_authenticated:
            # Отримуємо ID користувачів, на яких підписані
            following_users = Subscription.objects.filter(
                user_from=self.request.user
            ).values_list('user_to', flat=True)
            return Post.objects.filter(user__in=following_users).order_by('-date_published').select_related('user').prefetch_related('likes', 'comments')
        
        return Post.objects.all().order_by('-date_published').select_related('user').prefetch_related('likes', 'comments')
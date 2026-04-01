from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, DestroyAPIView, CreateAPIView
from .models import Post
from .serializers import *
from auth_system.models import Subscription
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework import status, parsers
from .permissions import *

class PostPagination(PageNumberPagination):
    page_size = 3  # Тільки для постів буде по 3
    page_size_query_param = 'page_size' # Дозволяє Android самому просити більше, якщо треба
    max_page_size = 100


class PingView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"status": "server works"})


class PostListAPIView(ListAPIView):
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


class PostCreateAPIView(APIView):
    # Тепер ми приймаємо не просто форму, а Multipart дані (файл + текст)
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request, *args, **kwargs):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            # Прив'язуємо юзера (як ти робив у form_valid)
            serializer.save(user=request.user) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # Передаємо pk поста в серіалізатор через дані
        serializer = LikeActionSerializer(data={'post': pk}, context={'request': request})
        
        if serializer.is_valid():
            # Наш кастомний save повертає статус
            instance, liked = serializer.save()
            
            # Нам все одно треба повернути кількість лайків для Android
            post_obj = Post.objects.get(pk=pk)
            
            return Response({
                'liked': liked,
                'likes_count': post_obj.likes.count()
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteCommentAPIView(DestroyAPIView):
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated, IsOwner]


class CommentCreateAPIView(CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Прив'язуємо поточного юзера автоматично
        serializer.save(user=self.request.user)
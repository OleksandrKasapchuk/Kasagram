from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from .models import Post
from .serializers import *
from .mixins import PostQuerysetMixin
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework import status, parsers
from common.permissions import *
from rest_framework.generics import RetrieveAPIView
from .models import Post
from .serializers import PostDetailSerializer 
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .models import Comment
from .serializers import CommentSerializer
from common.permissions import IsOwner 

class PingView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"status": "server works"})


class PostPagination(PageNumberPagination):
    page_size = 3  # Тільки для постів буде по 3
    page_size_query_param = 'page_size' # Дозволяє Android самому просити більше, якщо треба
    max_page_size = 100


class PostListAPIView(PostQuerysetMixin, ListAPIView):
    serializer_class = PostSerializer
    pagination_class = PostPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        return self.get_post_queryset()


class PostCreateAPIView(APIView):
    # Тепер ми приймаємо не просто форму, а Multipart дані (файл + текст)
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            # Прив'язуємо юзера (як ти робив у form_valid)
            serializer.save(user=request.user) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LikeAPIView(APIView):
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


class PostDetailAPIView(PostQuerysetMixin, RetrieveAPIView):
    serializer_class = PostDetailSerializer
    
    def get_queryset(self):
        # Використовуємо той самий метод, що і в списку постів
        return self.get_post_queryset()
    def get_serializer_context(self):
        # Це обов'язково для роботи request всередині SerializerMethodField
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context



class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


    def get_serializer_class(self):
        """
        Динамічно вибираємо серіалізатор:
        - Для оновлення (update, partial_update) беремо легкий BaseCommentSerializer (тільки content).
        - Для всього іншого (list, retrieve, create) — повний CommentSerializer.
        """
        if self.action in ['update', 'partial_update']:
            return BaseCommentSerializer
        return CommentSerializer
    
    def get_permissions(self):
        """
        Гнучко налаштовуємо права доступу:
        - Створення та читання: доступно будь-якому авторизованому юзеру.
        - Оновлення (update, partial_update) та Видалення (destroy): тільки власнику коментаря.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # Автоматично прив'язуємо автора коментаря
        serializer.save(user=self.request.user)

    def update(self, request, *x, **kwargs):
        """
        Кастомізуємо апдейт, щоб він приймав ЛІШЕ поле 'content' 
        і повертав чистий результат, як ти й хотів.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Беремо з запиту тільки 'content', щоб юзер випадково (або навмисно) 
        # не змінив post_id чи автора коментаря.
        data = {'content': request.data.get('content')}
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        # Повертаємо оновлений контент та статус 200
        return Response(serializer.data, status=status.HTTP_200_OK)
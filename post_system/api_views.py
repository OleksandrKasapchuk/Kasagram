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


class PostViewSet(PostQuerysetMixin, viewsets.ModelViewSet):
    """
    Об'єднаний в'юсет для постів:
    - Читання списку та детально (list, retrieve): AllowAny
    - Створення (create): IsAuthenticated
    - Видалення (destroy): IsAuthenticated + IsOwner
    """
    pagination_class = PostPagination
    # Додаємо парсери прямо сюди, щоб працювало завантаження медіа при створенні
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        # Використовуємо твій міксин для оптимізації запитів (select_related/prefetch_related)
        return self.get_post_queryset()

    def get_serializer_class(self):
        """
        Для детального перегляду (retrieve) використовуємо детальний серіалізатор,
        для списку (list) та створення (create) — базовий PostSerializer.
        """
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostSerializer

    def get_permissions(self):
        """
        Гнучкі права доступу для постів.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOwner]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny] # list та retrieve
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # Автоматично прив'язуємо поточного юзера як автора поста
        serializer.save(user=self.request.user)

    def get_serializer_context(self):
        # Передаємо request у контекст (треба для роботи SerializerMethodField в PostDetailSerializer)
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


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
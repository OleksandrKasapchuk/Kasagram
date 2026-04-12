from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, DestroyAPIView, CreateAPIView
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


class PostDetailAPIView(RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer
    
    def get_serializer_context(self):
        # Це обов'язково для роботи request всередині SerializerMethodField
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class DeleteCommentAPIView(DestroyAPIView):
    queryset = Comment.objects.all()
    permission_classes = [IsOwner]


class CommentCreateAPIView(CreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    def perform_create(self, serializer):
        # Прив'язуємо поточного юзера автоматично
        serializer.save(user=self.request.user)
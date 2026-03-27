from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Post
from .serializers import PostSerializer


class PingView(APIView):
    def get(self, request):
        return Response({"status": "server works"})
    


class PostListAPIView(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        # Це потрібно, щоб передати request у серіалізатор для поля is_liked
        return {'request': self.request}
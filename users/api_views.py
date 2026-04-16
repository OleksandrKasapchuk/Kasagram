from django.shortcuts import  get_object_or_404
from auth_system.models import CustomUser, Subscription
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from users.serializers import *
from rest_framework.decorators import action
from .serializers import UserSerializer 


class UserDetailAPIView(APIView):
    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        
        # Перетворюємо об'єкт юзера в JSON
        serializer = UserDetailSerializer(user)
        
        return Response(serializer.data)


class ToggleFollowAPIView(APIView):
    def post(self, request, pk):
        user_to = get_object_or_404(CustomUser, pk=pk)
        
        # Перевірка на підписку на самого себе
        if request.user == user_to:
            return Response(
                {'error': 'You cannot follow yourself.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription_qs = Subscription.objects.filter(
            user_from=request.user, 
            user_to=user_to
        )

        if subscription_qs.exists():
            subscription_qs.delete()
            following = False
        else:
            Subscription.objects.create(user_from=request.user, user_to=user_to)
            following = True
        
        return Response({
            'following': following,
            'followers_count': user_to.followers.count(),
            'following_count': user_to.following.count(),
        }, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserRelationshipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    # Ендпоінт: /api/users/<pk>/followers/
    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        user = self.get_object()
        # Отримуємо всіх, хто підписаний на цього юзера
        followers = CustomUser.objects.filter(following__user_to=user)
        
        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)

    # Ендпоінт: /api/users/<pk>/following/
    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        user = self.get_object()
        # Отримуємо всіх, на кого підписаний цей юзер
        following = CustomUser.objects.filter(followers__user_from=user)
        
        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data)
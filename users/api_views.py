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
        serializer = UserDetailSerializer(user, context={'request': request})
        
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
            follower=request.user, 
            following=user_to
        )

        if subscription_qs.exists():
            subscription_qs.delete()
            success = False
        else:
            Subscription.objects.create(follower=request.user, following=user_to)
            success = True
        
        return Response({
            'is_following': success,
            'followers_count': user_to.followers.count(),
            'following_count': user_to.following.count(),
        }, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserRelationshipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomUser.objects.all()
    def get_serializer_class(self):
        # Для перегляду конкретного профілю (retrieve) юзаємо повний дітейл
        if self.action == 'retrieve':
            return UserDetailSerializer
        # Для списків (list, followers, following) юзаємо легкий
        return UserSerializer

    # Ендпоінт: /api/users/<pk>/followers/
    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        user = self.get_object()
        followers = CustomUser.objects.filter(following__following=user)
        # get_serializer автоматично візьме UserSerializer з get_serializer_class
        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        user = self.get_object()
        following = CustomUser.objects.filter(followers__follower=user)
        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data)
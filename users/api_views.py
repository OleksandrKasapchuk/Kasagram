from django.shortcuts import  get_object_or_404
from auth_system.models import CustomUser, Subscription
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from users.serializers import *
from rest_framework.decorators import action
from .serializers import UserBaseSerializer 
from django.db.models import Count, Exists, OuterRef, Value, BooleanField


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
        serializer = UserBaseSerializer(request.user)
        return Response(serializer.data)


class UserRelationshipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomUser.objects.all()

    def get_queryset(self):
        """Централізована оптимізація всіх запитів"""
        user = self.request.user
        
        # 1. Базові анотації (лічильники потрібні скрізь)
        # Використовуємо distinct=True, щоб Count не перемножував дані через JOIN
        queryset = CustomUser.objects.annotate(
            posts_count=Count('posts', distinct=True),
            followers_count=Count('followers', distinct=True),
            followings_count=Count('following', distinct=True),
        )

        # 2. Анотація підписки (is_following_annotated)
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_following_annotated=Exists(
                    Subscription.objects.filter(follower=user, following=OuterRef('pk'))
                )
            )
        else:
            queryset = queryset.annotate(
                is_following_annotated=Value(False, output_field=BooleanField())
            )

        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserBaseSerializer

    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        # self.get_object() автоматично використає наш get_queryset() з усіма анотаціями
        user = self.get_object()
        
        # Беремо фоловерів і теж проганяємо їх через наш get_queryset
        # щоб у кожного юзера в списку теж був статус is_following (чи підписані МИ на них)
        followers = self.get_queryset().filter(following__following=user)
        
        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        user = self.get_object()
        
        # Аналогічно для тих, на кого підписаний юзер
        following = self.get_queryset().filter(followers__follower=user)
        
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data)
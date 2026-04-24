from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef, Case, When, BooleanField
from .models import Post, Like


class UserIsOwnerMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # Перевіряємо власника об'єкта (поля 'user' або 'author')
            owner = getattr(instance, 'user', getattr(instance, 'author', None))
            
            if owner and owner != request.user:
                raise PermissionDenied
        
        except:
            url_user_pk = kwargs.get('pk')
            if url_user_pk and str(url_user_pk) != str(request.user.pk):
                raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class PostQuerysetMixin:
    def get_post_queryset(self):
        # DRF автоматично об'єднує GET-параметри в query_params
        category = getattr(self.request, 'query_params', self.request.GET).get('category', 'for_you')
        user = self.request.user
        
        # 1. Базовий QuerySet з оптимізацією автора
        # Прибираємо prefetch_related('likes'), бо ми замінимо його на Exists
        queryset = Post.objects.select_related('user').all()

        # 2. Додаємо "розумні" поля через анотації (SQL рівень)
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_liked=Exists(
                    Like.objects.filter(user=user, post=OuterRef('pk'))
                ),
                is_owner=Case(
                    When(user=user, then=True),
                    default=False,
                    output_field=BooleanField()
                )
            )

            # 3. Фільтрація за категорією
            if category == 'following':
                # Замість values_list використовуємо фільтр прямо в основному запиті
                # Це перетвориться на красивий SQL JOIN або IN (SELECT ...)
                queryset = queryset.filter(
                    user__followers__follower=user
                ).distinct() # distinct потрібен, щоб уникнути дублів через JOIN

        return queryset.order_by('-date_published')
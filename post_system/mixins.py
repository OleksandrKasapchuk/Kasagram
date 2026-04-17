from django.core.exceptions import PermissionDenied
from .models import Post
from auth_system.models import Subscription


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
    """Спільна логіка фільтрації для Вебу та API"""
    def get_post_queryset(self):
        category = self.request.GET.get('category', 'for_you') # для Web
        if not category: # якщо GET порожній, перевіряємо query_params (для API)
            category = self.request.query_params.get('category', 'for_you')

        queryset = Post.objects.all().select_related('user').prefetch_related('likes', 'comments')

        if category == 'following' and self.request.user.is_authenticated:
            following_users = Subscription.objects.filter(
                follower=self.request.user
            ).values_list('following', flat=True)
            queryset = queryset.filter(user__in=following_users)
        
        return queryset.order_by('-date_published')

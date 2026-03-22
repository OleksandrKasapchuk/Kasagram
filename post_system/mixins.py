from django.core.exceptions import PermissionDenied

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

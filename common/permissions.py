from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Перевіряємо власника (поле user або author)
        owner = getattr(obj, 'user', getattr(obj, 'author', None))
        return owner == request.user
from rest_framework import permissions


class AuthorOrReadOnlyPermission(permissions.BasePermission):
    """
    Разрешение, которое позволяет только чтение для всех пользователей,
    но изменение только автору.
    """
    def has_permission(self, request, view):
        """Проверяет глобальные разрешения на уровне запроса."""
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Проверяет объектные разрешения на уровне экземпляра."""
        return (request.method in permissions.SAFE_METHODS
                or request.user == obj.author)

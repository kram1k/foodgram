from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """
    Класс разрешений, который предоставляет полный доступ автору объекта
    и только чтение остальным пользователям.
    """
    message = 'Только автор объекта может изменять его.'

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )

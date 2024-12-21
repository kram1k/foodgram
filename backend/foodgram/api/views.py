from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import TokenSerializer
from djoser.utils import login_user
from djoser.views import TokenCreateView
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    Tag
)
from users.models import User

from .filters import IngredientFilter, RecipeFilter
from .mixins import CreateListRetrieveViewSet
from .permissions import AuthorOrReadOnlyPermission
from .serializers import (
    Cart,
    FollowSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeLightSerializer,
    RecipeSerializer,
    SetPasswordSerializer,
    TagSerializer,
    UserSerializer
)


class UserViewSet(CreateListRetrieveViewSet):
    """Представление для работы с пользователями."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = PageNumberPagination

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        """Возвращает информацию о текущем пользователе."""
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def set_password(self, request):
        """Устанавливает новый пароль для текущего пользователя."""
        serializer = SetPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscriptions(self, request):
        """Возвращает список подписчиков текущего пользователя."""
        subscriptions = self.paginate_queryset(
            FollowSerializer(
                request.user.follower.all(),
                many=True,
                context={"request": request}
            ).data
        )
        return self.get_paginated_response(subscriptions)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, pk):
        """
        Подписывается или отписывается
        текущий пользователь на другого пользователя.
        """
        return self._handle_subscription(request, pk)

    def _handle_subscription(self, request, pk):
        """
        Обработчик подписки/отписки на другого пользователя.

        Аргументы:
            request (Request): Запрос от клиента.
            pk (int): Идентификатор пользователя,
            на которого нужно подписаться или отписаться.

        Возвращает:
            Response: Результат операции подписки/отписки.
        """
        current_user = request.user
        following = get_object_or_404(User, pk=pk)

        if request.method == "POST":
            if current_user == following:
                return self._error_response(
                    "Нельзя подписаться на самого себя")
            follow, created = Follow.objects.get_or_create(
                user=current_user, following=following
            )
            if not created:
                return self._error_response(
                    "Вы уже подписаны на этого пользователя"
                )
            return Response(
                FollowSerializer(follow, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        if current_user == following:
            return self._error_response("Вы не подписаны на самого себя")
        deleted, _ = Follow.objects.filter(
            user=current_user, following=following
        ).delete()
        if not deleted:
            return self._error_response(
                "Вы не были подписаны на этого пользователя"
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _error_response(self, message):
        """Возвращает ошибку с указанным сообщением."""
        return Response(
            {"errors": message},
            status=status.HTTP_400_BAD_REQUEST)


class CustomTokenCreateView(TokenCreateView):
    """
    Класс представления для создания токена аутентификации.

    Метод:
        _action(self, serializer):
        Обрабатывает создание токена после успешной проверки
        данных пользователя.

        Возвращает ответ с данными токена
        и статусом HTTP 201 CREATED.
    """
    def _action(self, serializer):
        return Response(
            data=TokenSerializer(
                login_user(self.request, serializer.user)
            ).data,
            status=status.HTTP_201_CREATED,
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Представление для просмотра ингредиентов.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Представление для просмотра тегов.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Представление для работы с рецептами.
    """
    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrReadOnlyPermission,)
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор
        в зависимости от метода запроса."""
        return RecipeCreateUpdateSerializer if self.request.method in (
            "POST", "PATCH"
        ) else RecipeSerializer

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk):
        """Добавляет или удаляет рецепт
        из избранного у текущего пользователя."""
        return self._handle_favorite_shopping_cart(request, pk, Favorite)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk):
        """Добавляет или удаляет рецепт
        из списка покупок текущего пользователя."""
        return self._handle_favorite_shopping_cart(request, pk, Cart)

    def _handle_favorite_shopping_cart(self, request, pk, model):
        """
        Обработчик добавления/удаления рецепта
        из избранного или списка покупок.

        Аргументы:
            request (Request): Запрос от клиента.
            pk (int): Идентификатор рецепта.
            model (Favorite|Cart): Модель для работы
            с избранным или списком покупок.

        Возвращает:
            Response: Ответ с результатом операции.
        """
        current_user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            obj, created = model.objects.get_or_create(
                user=current_user, recipe=recipe
            )
            if not created:
                return self._error_response(
                    f'Рецепт уже был добавлен в {model.__name__.lower()}.'
                )
            return Response(
                RecipeLightSerializer(obj.recipe).data,
                status=status.HTTP_201_CREATED)
        deleted, _ = model.objects.filter(
            user=current_user,
            recipe=recipe).delete()
        if not deleted:
            return self._error_response(
                f'Рецепта не было в {model.__name__.lower()}.'
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """
        Скачивание списка покупок в виде текстового файла.

        Аргументы:
            request (Request): Запрос от клиента.

        Возвращает:
            HttpResponse: Текстовый файл со списком покупок.
        """
        shopping_cart_qs = (
            IngredientRecipe.objects.filter(
                recipe__in_Cart_for_users__user=request.user
            )
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_count=Sum("amount"))
        )
        if not shopping_cart_qs.exists():
            return HttpResponse(
                "Список покупок ПУСТ",
                content_type="text/plain",
            )

        shopping_cart = [
            [
                ingredient['ingredient__name'],
                ingredient['ingredient__measurement_unit'],
                ingredient['total_count']
            ]
            for ingredient in shopping_cart_qs
        ]
        response = HttpResponse(
            render_to_string(
                'shopping_cart.txt',
                context={'shopping_cart': shopping_cart}),
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment;'
            ' filename=shopping_cart.txt'
        )
        return response

    def _error_response(self, message):
        """Формирует ответ с ошибкой."""
        return Response(
            {'errors': message},
            status=status.HTTP_400_BAD_REQUEST)

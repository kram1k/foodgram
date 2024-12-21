from rest_framework import mixins, viewsets


class CreateListRetrieveViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    Представление для создания, получения списка
    и получения отдельных экземпляров моделей.
    """
    pass

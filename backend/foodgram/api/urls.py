from django.urls import include, path
from rest_framework import routers

from .views import (
    CustomTokenCreateView,
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    UserViewSet
)

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'recipes', RecipeViewSet, basename='recipe')


urlpatterns = [
    path(
        'auth/token/login/',
        CustomTokenCreateView.as_view(),
        name='create_token'),
    path('auth/', include('djoser.urls.authtoken'), name='token'),
    path('', include(router.urls)),
]
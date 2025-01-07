from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.constants import PARAM_RECIPES_LIMIT_MIN_VALUE
from core.fields import Base64ImageField
from core.serializers import BaseUserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class RecipesLimitSerializer(serializers.Serializer):
    recipes_limit = serializers.IntegerField(
        required=False, min_value=PARAM_RECIPES_LIMIT_MIN_VALUE
    )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    author = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('short_link_code', 'created_at')

    def get_author(self, obj):
        return UserSerializer(
            obj.author,
            context=self.context
        ).data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Recipe
        exclude = (
            'short_link_code',
            'created_at'
        )

    def validate(self, data):
        errors = {}
        ingredients = self.initial_data.get('ingredients')
        if ingredients is None:
            errors['ingredients'] = 'Обязательное поле.'
        elif not ingredients:
            errors['ingredients'] = (
                'Необходимо указать хотя бы один ингредиент.'
            )
        else:
            ingredient_ids = [ingredient['id'] for ingredient in ingredients]
            if len(ingredient_ids) != len(set(ingredient_ids)):
                errors['ingredients'] = 'Ингредиенты не должны повторяться.'
        tags = self.initial_data.get('tags')
        if tags is None:
            errors['tags'] = 'Обязательное поле.'
        elif not tags:
            errors['tags'] = 'Необходимо указать хотя бы один тег.'
        elif len(tags) != len(set(tags)):
            errors['tags'] = 'Теги не должны повторяться.'
        image = self.initial_data.get('image')
        if not image:
            errors['image'] = 'Значение не должно быть пустым.'
        if errors:
            raise ValidationError(errors)
        return data

    def create(self, validated_data):
        return self.save_recipe(validated_data)

    def update(self, instance, validated_data):
        return self.save_recipe(validated_data, instance)

    def save_recipe(self, validated_data, instance=None):
        """Универсальная функция для создания и обновления."""
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe, _ = Recipe.objects.update_or_create(
            id=instance.id if instance else None,
            defaults=validated_data
        )
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])
        recipe.tags.set(tags)

        return recipe

    def to_representation(self, data):
        return (
            RecipeReadSerializer(
                context=self.context
            ).to_representation(data)
        )


class RecipeShortReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(BaseUserSerializer, DjoserUserSerializer):

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class AuthorSerializer(BaseUserSerializer):
    recipes = RecipeShortReadSerializer(many=True, source='limited_recipes')
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Subscription
        fields = '__all__'

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя.')
        if Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError('Вы уже подписаны на этого автора.')
        return data


class BaseUserRecipeSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        abstract = True
        fields = '__all__'

    def validate(self, data):
        if self.Meta.model.objects.filter(
            user=data['user'], recipe=data['recipe']
        ).exists():
            raise ValidationError('Рецепт уже добавлен.')
        return data


class ShoppingCartSerializer(BaseUserRecipeSerializer):

    class Meta(BaseUserRecipeSerializer.Meta):
        model = ShoppingCart


class FavoriteSerializer(BaseUserRecipeSerializer):

    class Meta(BaseUserRecipeSerializer.Meta):
        model = Favorite

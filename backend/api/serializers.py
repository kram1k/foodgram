import base64

from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import (
    Cart,
    Favorite,
    Follow,
    Ingredient,
    IngredientRecipe,
    Recipe,
    Tag
)
from users.models import User
from users.validators import validate_username

from .contsants import MAX_CHAR_LENGHT, MIN_AMOUNT, RECIPES_LIMIT


class Base64ImageField(serializers.ImageField):
    """Поле для загрузки изображений в формате base64."""
    def to_internal_value(self, data):
        """Преобразует строку base64 в объект ImageField."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeLightSerializer(serializers.ModelSerializer):
    """Уменьшенная версия сериализатора для рецептов."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = ('id', 'name', 'image', 'cooking_time',)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""
    is_subscribed = serializers.SerializerMethodField()
    first_name = serializers.CharField(max_length=MAX_CHAR_LENGHT)
    second_name = serializers.CharField(max_length=MAX_CHAR_LENGHT)
    password = serializers.CharField(
        max_length=MAX_CHAR_LENGHT,
        write_only=True,
        validators=[validate_password]
    )
    username = serializers.SlugField(
        max_length=MAX_CHAR_LENGHT,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким username уже существует'),
            validate_username
        ],
    )
    email = serializers.EmailField(
        max_length=MAX_CHAR_LENGHT,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='Пользователь с таким email уже существует'
            )
        ]
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed'
        )

    def create(self, validated_data):
        """Создает нового пользователя."""
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_is_subscribed(self, obj):
        """Определяет, подписан ли текущий пользователь на данного автора."""
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=current_user,
            following=obj
        ).exists()


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""
    new_password = serializers.CharField(
        max_length=MAX_CHAR_LENGHT,
        write_only=True,
        validators=[validate_password])
    current_password = serializers.CharField()

    def validate(self, data):
        """Валидация введённых данных перед изменением пароля."""
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError(
                'Введите новый пароль, отличный от существующего!')
        if not self.context.get('request').user.check_password(
                data['current_password']):
            raise serializers.ValidationError(
                'Введенный существующий пароль неверный')
        return data


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки на пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')

    class Meta:
        model = Follow
        fields = '__all__'

    def get_is_subscribed(self, obj):
        """Определяет, подписан ли текущий пользователь на данного автора."""
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return Follow.objects.filter(user=current_user,
                                     following=obj.following).exists()

    def get_recipes(self, obj):
        """Возвращает ограниченное количество рецептов автора."""
        recipes_limit = (
            self.context.get('request').query_params.get('recipes_limit')
        )
        if recipes_limit is None:
            recipes_limit = RECIPES_LIMIT
        return RecipeLightSerializer(
            obj.following.recipes.all()[:int(recipes_limit)],
            many=True
        ).data

    def get_recipes_count(self, obj):
        """ Возвращает общее количество рецептов автора."""
        return obj.following.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тега."""
    class Meta:
        model = Tag
        lookup_field = 'slug'
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента."""
    class Meta:
        model = Ingredient
        lookup_field = 'slug'
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для связи между ингредиентами и рецептами."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)

    class Meta:
        model = IngredientRecipe
        fields = '__all__'

    def to_representation(self, instance):
        """
        Переопределяем стандартный метод `to_representation` для корректной
        обработки поля `id`.
        """
        data = (super(
            IngredientRecipeSerializer,
            self
        ).to_representation(instance))
        data['id'] = instance.ingredient.id
        return data


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(
        many=True,
        source='ingredients_in_recipe'
    )

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        """
        Определяет, находится ли рецепт
        в избранном у текущего пользователя.
        """
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return Favorite.objects.filter(user=current_user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Определяет, находится ли рецепт
        всписке покупок текущего пользователя.
        """
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return (Cart.objects.filter(
            user=current_user,
            recipe=obj).exists()
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    ingredients = IngredientRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate_ingredients(self, value):
        """Проверка валидности ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один ингредиент!')
        ingredients_list = [ingredient.get('id') for ingredient in value]
        if len(set(ingredients_list)) < len(ingredients_list):
            raise serializers.ValidationError(
                f'Выбранные ингредиенты повторяются! {ingredients_list}')
        return value

    def get_ingredients_data(self, ingredients, recipe):
        """Формирование данных для ингредиентов."""
        ingredients_data = []
        for ingredient_orderdict in ingredients:
            recipe_ingredient = IngredientRecipe(
                ingredient=ingredient_orderdict.get('id'),
                recipe=recipe,
                amount=ingredient_orderdict.get('amount')
            )
            ingredients_data.append(recipe_ingredient)
        return ingredients_data

    def to_representation(self, instance):
        """Преобразование данных в формат для вывода."""
        return RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data

    def create(self, validated_data):
        """Создание нового рецепта."""
        current_user = self.context.get('request').user
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=current_user)
        recipe.tags.set(tags)
        ingredients_data = self.get_ingredients_data(ingredients, recipe)
        IngredientRecipe.objects.bulk_create(ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            ingredients_data = self.get_ingredients_data(ingredients, instance)
            instance.ingredients.clear()
            IngredientRecipe.objects.bulk_create(ingredients_data)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)
            super().update(instance, validated_data)
        return instance

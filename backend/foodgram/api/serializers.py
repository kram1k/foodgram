import base64

from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from users.models import User
from recipes.models import (
    Tag,
    Recipe,
    Ingredient,
    IngredientRecipe
)

from .contsants import MAX_CODE_LENGHT


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, validators=[])
    email = serializers.EmailField(required=True, validators=[])

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'role',
        )

    def create(self, validated_data):
        user, created = User.objects.get_or_create(
            email=validated_data['email'], defaults=validated_data
        )
        if created:
            confirmation_code = get_random_string(length=MAX_CODE_LENGHT)
            user.confirmation_code = confirmation_code
            user.save()
        return user

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        existing_user = User.objects.filter(
            email=email, username=username
        ).first()
        if existing_user:
            return data
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Адрес электронной почты уже существует.'
            )
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Имя пользователя уже существует.'
            )
        return data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        exclude = ('id',)
        lookup_field = 'slug'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        exclude = ('id',)
        lookup_field = 'slug'


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    tag = SlugRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        slug_field='slug',
        allow_null=False,
        allow_empty=False,
    )
    ingredient = SlugRelatedField(
        queryset = Ingredient.objects.all()
    )
    image = Base64ImageField(required=False, allow_null=True)
    class Meta:
        model = Recipe
        fields = '__all__'

    def create(self, validated_data):
        if 'ingredient' not in self.initial_data:
            recipe = Recipe.objects.create(**validated_data)
            return recipe
        ingredients = validated_data.pop('ingredient')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            current_ingredient, status = Ingredient.objects.get_or_create(
                **ingredient
            )
        IngredientRecipe.objects.create(
            ingredient=current_ingredient, recipe=recipe
        )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.description = validated_data.get('description', instance.description)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)     
        if 'ingredient' not in validated_data:
            instance.save()
            return instance
        ingredient_data = validated_data.pop('ingredient')
        lst = []
        for ingredient in ingredient_data:
            current_ingredient, status = Ingredient.objects.get_or_create(
                **ingredient
            )
            lst.append(current_ingredient)
        instance.ingredients.set(lst)

        instance.save()
        return instance

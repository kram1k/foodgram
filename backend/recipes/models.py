from textwrap import shorten

from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator, MinValueValidator
from django.db import models

from core.constants import (INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
                            INGREDIENT_NAME_MAX_LENGTH,
                            OBJECT_NAME_MAX_DISPLAY_LENGTH,
                            RECIPE_COOKING_TIME_MIN_VALUE,
                            RECIPE_INGREDIENT_AMOUNT_MIN_VALUE,
                            RECIPE_NAME_MAX_LENGTH,
                            RECIPE_TEXT_MAX_LENGTH,
                            RECIPE_SHORT_LINK_CODE_MAX_LENGTH,
                            TAG_NAME_MAX_LENGTH, TAG_SLUG_MAX_LENGTH)

from .utils import make_relation_name

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=INGREDIENT_NAME_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='uq_recipes_ingredient_name_measurement_unit'
            ),
        )
        db_table = 'recipes_ingredient'

    def __str__(self):
        short_name = shorten(
            self.name,
            width=OBJECT_NAME_MAX_DISPLAY_LENGTH,
            placeholder=' ...'
        )
        return f'{short_name} ({self.measurement_unit})'


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=TAG_NAME_MAX_LENGTH
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)
        db_table = 'recipes_tag'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=RECIPE_NAME_MAX_LENGTH,
        unique=True,
        validators=[
            MaxLengthValidator(
                limit_value=RECIPE_NAME_MAX_LENGTH,
                message='Максимальная длина названия рецепта - 150 символов.',
            )
        ]
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipe_images'
    )
    text = models.TextField(
        verbose_name='Описание',
        validators=[
            MaxLengthValidator(
                limit_value=RECIPE_TEXT_MAX_LENGTH,
                message='Максимальное количество символов описания - 5000.',
            )
        ]
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='RecipeIngredient'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        help_text='В минутах',
        validators=[
            MinValueValidator(
                limit_value=RECIPE_COOKING_TIME_MIN_VALUE,
                message='Минимальное время приготовления - 10 минут.',
            )
        ]
    )
    short_link_code = models.CharField(
        verbose_name='Код короткой ссылки',
        max_length=RECIPE_SHORT_LINK_CODE_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        verbose_name='Дата и время публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-created_at',)
        db_table = 'recipes_recipe'

    def __str__(self):
        return shorten(
            self.name,
            width=OBJECT_NAME_MAX_DISPLAY_LENGTH,
            placeholder=' ...'
        )


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='ingredient_recipes'
    )
    amount = models.IntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(
                RECIPE_INGREDIENT_AMOUNT_MIN_VALUE,
                message=(
                    'Количество ингредиента не может быть меньше '
                    f'{RECIPE_INGREDIENT_AMOUNT_MIN_VALUE}.'
                )
            ),
        )
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='uq_recipes_recipe_ingredients'
            ),
        )
        ordering = ('recipe__name', 'ingredient__name')
        db_table = 'recipes_recipe_ingredients'

    def __str__(self):
        return make_relation_name(self.recipe, self.ingredient)


class BaseUserRecipe(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='%(class)s_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='%(class)s_users'
    )

    class Meta:
        abstract = True
        ordering = ('user__username', 'recipe__name')

    def __str__(self):
        return make_relation_name(self.user, self.recipe)


class ShoppingCart(BaseUserRecipe):

    class Meta(BaseUserRecipe.Meta):
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Корзина'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='uq_recipes_shopping_carts'
            ),
        )
        db_table = 'recipes_shopping_carts'


class Favorite(BaseUserRecipe):

    class Meta(BaseUserRecipe.Meta):
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='uq_recipes_favorites'
            ),
        )
        db_table = 'recipes_favorites'

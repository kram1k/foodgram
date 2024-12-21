from django.core.validators import MinValueValidator
from django.db import models

from users.models import User

from .constants import (
    MAX_LEN_DESCRIP,
    MAX_LEN_NAME,
    MIN_AMOUNT_ING,
    UNIT_MEASURES
)


class BaseModel(models.Model):
    name = models.CharField(
        max_length=MAX_LEN_NAME,
    )


class Recipe(BaseModel):
    """Модель рецепта"""
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None,
        verbose_name='Изображение'
    )
    description = models.CharField(
        max_length=MAX_LEN_DESCRIP,
        verbose_name='Описание'
    )
    tag = models.ManyToManyField(
        'Tag',
        related_name='tags',
        verbose_name='Тэг'
    )
    ingredient = models.ManyToManyField(
        'Ingredient',
        related_name='ingredients',
        verbose_name='Ингредиент'
    )
    cooking_time = models.TimeField()
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_created=True,
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']

    def __str__(self):
        return self.name


class Tag(BaseModel):
    """Модель тега"""
    slug = models.SlugField(
        max_length=MAX_LEN_NAME,
        unique=True,
        db_index=True,
        verbose_name='slug'
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(BaseModel):
    """Модель ингредиента"""
    unit_of_measurement = models.CharField(
        max_length=25,
        choices=UNIT_MEASURES,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Модель ингредиентов в рецептах"""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        default=MIN_AMOUNT_ING,
        verbose_name='Количество',
        validators=[MinValueValidator(
            MIN_AMOUNT_ING,
            message='Количество ингредиента должно быть не меньше 1'
        )]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} {self.recipe} {self.amount}'


class Favorite(models.Model):
    """Модель избранных рецептов у пользователей"""
    user = models.ForeignKey(
        User,
        related_name='favorite_recipes',
        on_delete=models.CASCADE,
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorite_for_users',
        on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class Cart(models.Model):
    """Модель списка покупок у пользователей"""
    user = models.ForeignKey(
        User,
        related_name='recipes_in_shoppingcart',
        on_delete=models.CASCADE,
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_shoppingcart_for_users',
        on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppinglist_user_recipe'
            )
        ]


class Follow(models.Model):
    """Модель подписок у пользователей"""
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик')
    following = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='user_and_following_different'),
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follow'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.following}'

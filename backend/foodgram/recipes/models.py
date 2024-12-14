from django.db import models

from users.models import User

from .constants import (
    MAX_LEN_NAME,
    MAX_LEN_DESCRIP,
    UNIT_MEASURES
)


class BaseModel(models.Model):
    name = models.CharField(
        max_length=MAX_LEN_NAME,
    )


class Recipe(BaseModel):
    """Модель рецепта"""
    user = User
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

    def __str__(self):
        return self.name


class Tag(BaseModel):
    """Модель тега"""
    slug = models.SlugField(
        unique=True,
        db_index=True,
        verbose_name='slug'
    )

    def __str__(self):
        return self.name


class Ingredient(BaseModel):
    """Модель ингредиента"""
    unit_of_measurement = models.CharField(
        max_length=25,
        choices=UNIT_MEASURES
    )

    def __str__(self):
        return self.name

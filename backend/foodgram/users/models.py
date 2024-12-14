from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

from .constants import (
    MAX_CODE_LENGHT,
    MAX_NAME_LENGHT,
    ADMIN,
    MODERATOR,
    USER
)
from .validators import validate_username


class User(AbstractUser):
    """Модель пользователя."""

    confirmation_code = models.CharField(
        max_length=MAX_CODE_LENGHT, blank=True, null=True
    )
    role = models.CharField(
        max_length=MAX_NAME_LENGHT,
        choices=[
            (ADMIN, 'Admin'),
            (MODERATOR, 'Moderator'),
            (USER, 'User'),
        ],
        default=USER,
    )
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=MAX_NAME_LENGHT,
        unique=True,
        validators=[validate_username],
    )

    groups = models.ManyToManyField(
        Group,
        related_name='user_custom_groups',
        blank=True,
    )

    user_permissions = models.ManyToManyField(
        Permission,
        related_name='user_custom_permissions',
        blank=True,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role == MODERATOR
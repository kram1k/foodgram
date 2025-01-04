from textwrap import shorten

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from recipes.utils import make_relation_name

from .constants import (
    OBJECT_NAME_MAX_DISPLAY_LENGTH,
    USER_EMAIL_MAX_LENGTH,
    USER_NAME_MAX_LENGTH
)


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField(
        verbose_name='Email',
        max_length=USER_EMAIL_MAX_LENGTH,
        unique=True,
    )
    username = models.CharField(
        verbose_name='Логин',
        max_length=USER_NAME_MAX_LENGTH,
        unique=True,
        validators=(UnicodeUsernameValidator(),)
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=USER_NAME_MAX_LENGTH
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=USER_NAME_MAX_LENGTH
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/avatars/',
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = 'Объект "Пользователь"'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        db_table = 'users_user'

    def __str__(self):
        return shorten(
            self.username,
            width=OBJECT_NAME_MAX_DISPLAY_LENGTH,
            placeholder=' ...'
        )


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='subscription_authors'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='subscription_users'
    )

    class Meta:
        verbose_name = 'Объект "Подписка"'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='uq_users_subscriptions'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='chk_users_subscriptions_prevent_self_subscription'
            )
        )
        ordering = ('user__username', 'author__username')
        db_table = 'users_subscriptions'

    def __str__(self):
        return make_relation_name(self.user, self.author)

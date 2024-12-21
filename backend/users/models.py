from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy

from .constants import MAX_NAME_LENGHT
from .validators import validate_username


class User(AbstractUser):
    """ Модель пользователя, расширяющая стандартную модель Django User."""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    email = models.EmailField(
        ugettext_lazy('email address'),
        unique=True
    )
    username = models.CharField(
        ugettext_lazy('username'),
        max_length=MAX_NAME_LENGHT,
        unique=True,
        validators=[validate_username]
    )

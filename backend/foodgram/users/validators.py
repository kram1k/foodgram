import re

from django.core.exceptions import ValidationError

from .constants import REGULAR_CHECK_LOGIN_VALID, USERNAME_ME


def validate_username(username):
    if username == USERNAME_ME:
        raise ValidationError('Зарезервированный логин, нельзя использовать')
    if not re.match(REGULAR_CHECK_LOGIN_VALID, username):
        raise ValidationError(
            'В логине нельзя использовать символы, отличные от букв'
            'в верхнем и нижнем регистрах, цифр, знаков подчеркивания,'
            'точки, знаков плюса, минуса и собаки (@)'
        )
    return username
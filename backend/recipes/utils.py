import secrets
from textwrap import shorten

from core.constants import (
    OBJECT_NAME_MAX_DISPLAY_LENGTH,
    RECIPE_SHORT_LINK_CODE_MAX_LENGTH
)


def generate_unique_short_link_code():
    from .models import Recipe
    while True:
        random_code = (
            secrets.token_urlsafe().replace('_', '').replace('-', '')[
                :RECIPE_SHORT_LINK_CODE_MAX_LENGTH
            ].lower()
        )
        if not Recipe.objects.filter(short_link_code=random_code).exists():
            return random_code


def make_relation_name(obj_1, obj_2):
    return (
        shorten(
            str(obj_1),
            width=OBJECT_NAME_MAX_DISPLAY_LENGTH // 2,
            placeholder=' ...'
        )
        + ' - '
        + shorten(
            str(obj_2),
            width=OBJECT_NAME_MAX_DISPLAY_LENGTH // 2,
            placeholder=' ...'
        )
    )

from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.html import format_html

from api.contsants import MIN_AMOUNT

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

class RecipeIngredientFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        has_ingredients = any(
            not form.cleaned_data.get('DELETE', False)
            for form in self.forms
            if form.cleaned_data
        )
        if not has_ingredients:
            self.non_form_errors().append(
                'Рецепт не может быть без ингредиентов.'
            )


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    formset = RecipeIngredientFormSet
    extra = 0
    min_num = MIN_AMOUNT

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview',
        'name',
        'author_link',
        'cooking_time',
        'ingredients_list',
        'favorites_count'
    )
    list_display_links = ('image_preview', 'name')
    search_fields = (
        'name',
        'author__username',
        'author__first_name',
        'author__last_name',
        'author__email'
    )
    list_filter = ('tags',)
    readonly_fields = ('author', 'short_link_code', 'created_at')
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInline,)
    ordering = ('-created_at',)

    @admin.display(description='Изображение')
    def image_preview(self, obj):
        return format_html(
            (
                '<img src="{}" style="width: 50px; height: 50px;'
                'object-fit: contain;" />'
            ),
            obj.image.url
        )

    def save_model(self, request, obj, form, change):
        if not hasattr(obj, 'author'):
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorite_users.count()

    @admin.display(description='Автор')
    def author_link(self, obj):
        url = reverse(
            'admin:users_user_change', args=(obj.author.id,)
        )
        return format_html('<a href="{}">{}</a>', url, obj.author)

    @admin.display(description='Ингредиенты')
    def ingredients_list(self, obj):
        return ', '.join(
            str(ingredient) for ingredient in obj.ingredients.all()
        )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    ordering = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    ordering = ('recipe__name', 'ingredient__name')


class BaseUserRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    ordering = ('user__username', 'recipe__name')


@admin.register(Favorite)
class FavoriteAdmin(BaseUserRecipeAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(BaseUserRecipeAdmin):
    pass

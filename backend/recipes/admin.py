from django.contrib import admin

from .models import (
    Favorite,
    Follow,
    Ingredient,
    Recipe,
    IngredientRecipe,
    Cart,
    Tag
)


class IngredientInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1
    verbose_name_plural = 'Ингредиенты'
    verbose_name = 'Ингредиент'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'unit_of_measurement',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug',)


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'following')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'author',
        'description',
        'cooking_time',
        'added_in_favorite'
    )
    list_filter = ('tag',)
    search_fields = ('name', 'author__email')
    inlines = [IngredientInline]

    @admin.display(description='Количество добавлений в Избранное')
    def added_in_favorite(self, obj):
        return obj.favorite_for_users.count()

from django import forms
from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.templatetags.static import static
from django.utils.html import format_html

from recipes.models import Favorite, ShoppingCart

from .models import Subscription, User


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['user'] == cleaned_data['author']:
            self.add_error('author', 'Нельзя подписаться на самого себя.')
        return cleaned_data


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    form = SubscriptionForm
    fk_name = 'user'
    extra = 0
    verbose_name = 'объект "Подписка"'
    verbose_name_plural = 'Подписки'


class FavoriteInline(admin.TabularInline):
    model = Favorite
    fk_name = 'user'
    extra = 0
    verbose_name = 'Избранный рецепт'
    verbose_name_plural = 'Избранные рецепты'


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    fk_name = 'user'
    extra = 0
    verbose_name = 'Рецепт в корзине'
    verbose_name_plural = 'Рецепты в корзине'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'avatar_preview',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_staff',
        'is_active',
        'is_superuser',
        'subscriptions_count',
        'subscribers_count',
        'favorite_recipes_count'
    )
    list_display_links = ('avatar_preview', 'username')
    search_fields = (
        'name',
        'username',
        'first_name',
        'last_name',
        'email'
    )
    list_filter = (
        'is_staff',
        'is_active',
        'is_superuser'
    )
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('avatar',)
        }),
    )
    inlines = (SubscriptionInline, FavoriteInline, ShoppingCartInline)
    ordering = ('username',)

    @display(description='Аватар')
    def avatar_preview(self, obj):
        url = (
            obj.avatar.url
            if obj.avatar
            else static('images/avatar_placeholder.png')
        )
        return format_html(
            (
                '<img src="{}" style="width: 50px; height: 50px;'
                'object-fit: contain;" />'
            ),
            url
        )

    @display(description='Подписок')
    def subscriptions_count(self, obj):
        return obj.subscriptions.count()

    @display(description='Подписчиков')
    def subscribers_count(self, obj):
        return obj.subscribed_by.count()

    @display(description='Избранных рецептов')
    def favorite_recipes_count(self, obj):
        return obj.favorite_recipes.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
    ordering = ('user__username', 'author__username')

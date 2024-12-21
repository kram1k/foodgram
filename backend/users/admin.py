from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class CustomUserAdmin(UserAdmin):
    list_display = [
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',]


admin.site.register(User, UserAdmin)

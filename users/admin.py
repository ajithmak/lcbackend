"""users/admin.py — Register User model with Django admin."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ['email', 'name', 'phone', 'is_staff', 'is_active', 'date_joined']
    list_filter    = ['is_staff', 'is_active']
    search_fields  = ['email', 'name', 'phone']
    ordering       = ['-date_joined']
    readonly_fields= ['date_joined']

    fieldsets = (
        (None,           {'fields': ('email', 'password')}),
        ('Personal',     {'fields': ('name', 'phone', 'address')}),
        ('Permissions',  {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps',   {'fields': ('date_joined',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':  ('email', 'name', 'password1', 'password2'),
        }),
    )

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("role", "phone", "department")}),
    )
    list_display = ("username", "email", "role", "department", "is_staff", "is_active")
    list_filter = ("role", "department", "is_staff", "is_superuser", "is_active")

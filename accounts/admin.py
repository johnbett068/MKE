from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Account, AccountRole, OneTimeCode, Profile, Role


@admin.register(Account)
class AccountAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "phone_number", "is_staff", "is_active")
    search_fields = ("email", "phone_number", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "phone_number")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )
    filter_horizontal = ()


admin.site.register(Role)
admin.site.register(AccountRole)
admin.site.register(Profile)


@admin.register(OneTimeCode)
class OneTimeCodeAdmin(admin.ModelAdmin):
    list_display = ("account", "purpose", "expires_at", "consumed_at")
    readonly_fields = (
        "account", "purpose", "code_hash", "expires_at", "attempts",
        "consumed_at", "created_at",
    )
    def has_add_permission(self, request):
        return False

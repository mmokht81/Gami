from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, OTP

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        "phone_number",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "is_staff",
        "is_active",
    )

    ordering = ("phone_number",)

    search_fields = (
        "phone_number",
        "first_name",
        "last_name",
    )

    fieldsets = (
        (None, {
            "fields": (
                "phone_number",
                "password",
            )
        }),
        ("Personal Info", {
            "fields": (
                "first_name",
                "last_name",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important Dates", {
            "fields": (
                "last_login",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "phone_number",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "code",
        "is_used",
        "created_at",
        "expires_at",
    )

    search_fields = (
        "phone_number",
    )

    list_filter = (
        "is_used",
    )

    ordering = (
        "-created_at",
    )
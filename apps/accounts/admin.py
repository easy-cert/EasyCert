from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm, CustomUserChangeForm

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for our email-based User model."""
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    
    list_display = ["email", "full_name", "role", "barangay", "is_active", "date_joined"]
    list_filter = ["role", "barangay", "is_active", "is_staff"]
    search_fields = ["email", "full_name", "contact_number"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "contact_number", "address", "age", "birthdate")}),
        ("Role & Barangay", {"fields": ("role", "barangay")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("date_joined", "last_login")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "password1", "password2", "role", "barangay"),
        }),
    )
from django.contrib import admin
from .models import Barangay, BarangayMembership


@admin.register(Barangay)
class BarangayAdmin(admin.ModelAdmin):
    list_display = ["barangay_name", "captain_name", "location", "contact", "is_active"]
    list_filter = ["is_active", "location"]
    search_fields = ["barangay_name", "captain_name"]


@admin.register(BarangayMembership)
class BarangayMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "barangay", "status", "date_applied", "date_reviewed", "reviewed_by"]
    list_filter = ["status", "barangay"]
    search_fields = ["user__full_name", "user__email", "barangay__barangay_name"]
    readonly_fields = ["date_applied", "date_reviewed"]

from django.contrib import admin
from .models import CertificateRequest


@admin.register(CertificateRequest)
class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = [
        "tracking_number", "get_display_name", "certificate_type",
        "status", "appointment_time", "date_requested",
    ]
    list_filter = ["status", "certificate_type", "date_requested"]
    search_fields = ["tracking_number", "first_name", "last_name"]
    readonly_fields = ["tracking_number", "date_requested"]
    list_per_page = 30

    @admin.display(description="Applicant Name", ordering="last_name")
    def get_display_name(self, obj):
        return obj.display_name

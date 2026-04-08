from django.contrib import admin
from .models import CertificateRequest


@admin.register(CertificateRequest)
class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = [
        "tracking_number", "get_display_name", "certificate_type",
        "get_barangay", "status", "appointment_time", "date_requested",
        "reviewed_by",
    ]
    list_filter = ["status", "certificate_type", "barangay", "date_requested"]
    search_fields = ["tracking_number", "first_name", "last_name"]
    readonly_fields = ["tracking_number", "date_requested"]
    list_per_page = 30

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("barangay", "user", "reviewed_by")
        # Data isolation: Barangay admins only see their own barangay
        if hasattr(request.user, 'is_barangay_admin') and request.user.is_barangay_admin:
            if request.user.barangay:
                qs = qs.filter(barangay=request.user.barangay)
        return qs

    @admin.display(description="Applicant Name", ordering="last_name")
    def get_display_name(self, obj):
        return obj.display_name

    @admin.display(description="Barangay", ordering="barangay__barangay_name")
    def get_barangay(self, obj):
        return obj.barangay.barangay_name


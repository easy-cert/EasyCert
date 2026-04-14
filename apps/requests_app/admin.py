from django.contrib import admin
from django.utils.html import format_html
from .models import CertificateRequest, SupportTicket


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


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("resident_name", "concern_type", "status", "view_attachment", "created_at")
    list_filter = ("status", "concern_type", "created_at")
    search_fields = ("user__email", "user__full_name", "message")
    readonly_fields = ("created_at", "updated_at")

    def resident_name(self, obj):
        return obj.user.full_name if obj.user else "Anonymous"

    @admin.display(description="Attachment")
    def view_attachment(self, obj):
        # Prefer the Blob URL, fallback to local FileField URL
        url = obj.attachment_url or (obj.attachment.url if obj.attachment else None)
        if url:
            return format_html(
                '<a href="{}" target="_blank" style="color: #2c7be5; font-weight: bold;">Open File</a>',
                url
            )
        return "No file"


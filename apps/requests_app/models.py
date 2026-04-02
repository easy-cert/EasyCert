from django.db import models
from django.conf import settings
from apps.barangays.models import Barangay
import random


class CertificateRequest(models.Model):
    """
    A single model for ALL certificate types.
    Certificate-specific fields are stored in the `form_data` JSONField.
    This is flexible and avoids creating 8 separate models.
    """

    CERTIFICATE_TYPES = [
        ("Cedula", "Cedula"),
        ("Barangay Clearance", "Barangay Clearance"),
        ("Barangay Residency", "Barangay Residency"),
        ("Barangay Indigency", "Barangay Indigency"),
        ("Certificate of Low Income", "Certificate of Low Income"),
        ("Certificate for No Income", "Certificate for No Income"),
        ("Business Permit", "Business Permit"),
        ("Barangay Identification", "Barangay Identification"),
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    APPOINTMENT_CHOICES = [
        ("7:30 AM", "7:30 AM"),
        ("9:00 AM", "9:00 AM"),
        ("10:30 AM", "10:30 AM"),
        ("1:30 PM", "1:30 PM"),
        ("3:00 PM", "3:00 PM"),
        ("4:30 PM", "4:30 PM"),
    ]

    # -- Core fields --
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificate_requests",
        null=True,
        blank=True,  # allow anonymous / walk-in requests
    )
    barangay = models.ForeignKey(
        Barangay,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    certificate_type = models.CharField(max_length=50, choices=CERTIFICATE_TYPES)
    tracking_number = models.CharField(max_length=30, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    # -- Applicant info (common fields stored directly) --
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, default="")
    sitio = models.CharField("Sitio / Zone / Address", max_length=200, blank=True, default="")
    purpose = models.CharField(max_length=150, blank=True, default="")

    # -- Extra / certificate-specific data (flexible JSON) --
    form_data = models.JSONField(default=dict, blank=True)

    # -- Appointment --
    appointment_time = models.CharField(max_length=20, choices=APPOINTMENT_CHOICES)

    # -- Admin notes --
    admin_notes = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_requests",
    )

    # -- Timestamps --
    date_requested = models.DateTimeField(auto_now_add=True)
    date_reviewed = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_requested"]
        db_table = "certificate_requests"

    def __str__(self):
        return f"{self.tracking_number} — {self.certificate_type} ({self.status})"

    @property
    def display_name(self):
        mn_initial = f" {self.middle_name[0]}." if self.middle_name else ""
        return f"{self.last_name}, {self.first_name}{mn_initial}"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self._generate_tracking()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_tracking():
        import datetime
        year = datetime.date.today().year
        for _ in range(10):
            num = random.randint(10000, 99999)
            candidate = f"EC-{year}-{num}"
            if not CertificateRequest.objects.filter(tracking_number=candidate).exists():
                return candidate
        # Fallback: use a longer random number to virtually eliminate collisions
        num = random.randint(100000, 999999)
        return f"EC-{year}-{num}"
from django.db import models
from django.conf import settings
from django.utils import timezone


class Barangay(models.Model):
    """Represents a single barangay unit."""
    barangay_name = models.CharField(max_length=100, unique=True)
    location      = models.CharField(max_length=200, default="Cebu City")
    captain_name  = models.CharField(max_length=150)
    contact       = models.CharField(max_length=20, blank=True, default="")
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "barangays"
        verbose_name_plural = "Barangays"
        ordering = ["barangay_name"]

    def __str__(self):
        return self.barangay_name


class BarangayMembership(models.Model):
    """
    Tracks a user's request to join a barangay.
    Must be approved by the barangay admin before the user
    can submit certificate requests to that barangay.
    """
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    STATUS_CHOICES = [
        (PENDING, "Pending Review"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]

    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    barangay    = models.ForeignKey(
        Barangay,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    status      = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reviewed_memberships",
    )
    admin_notes   = models.TextField(blank=True, default="")
    date_applied  = models.DateTimeField(auto_now_add=True)
    date_reviewed = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "barangay_memberships"
        unique_together = ["user", "barangay"]
        ordering = ["-date_applied"]

    def __str__(self):
        return f"{self.user.full_name} → {self.barangay.barangay_name} ({self.status})"

    @property
    def is_pending(self):
        return self.status == self.PENDING

    @property
    def is_approved(self):
        return self.status == self.APPROVED

    def approve(self, admin_user):
        """Approve and assign the barangay to the user."""
        self.status = self.APPROVED
        self.reviewed_by = admin_user
        self.date_reviewed = timezone.now()
        self.save()
        # Also set the user's active barangay
        self.user.barangay = self.barangay
        self.user.save(update_fields=["barangay"])

    def reject(self, admin_user, notes=""):
        """Reject the membership request."""
        self.status = self.REJECTED
        self.reviewed_by = admin_user
        self.admin_notes = notes
        self.date_reviewed = timezone.now()
        self.save()
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", "superadmin")
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    # ── Role constants ──
    USER       = "user"
    ADMIN      = "admin"
    SUPERADMIN = "superadmin"
    ROLE_CHOICES = [
        (USER, "Resident"),
        (ADMIN, "Barangay Admin"),
        (SUPERADMIN, "Super Admin"),
    ]

    # ── Identity ──
    email          = models.EmailField(unique=True)
    full_name      = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20, blank=True, default="")

    # ── New profile fields (Phase 1) ──
    address        = models.CharField(max_length=300, blank=True, default="")
    age            = models.PositiveIntegerField(null=True, blank=True)
    birthdate      = models.DateField(null=True, blank=True)
    position       = models.CharField(max_length=100, blank=True, default="", help_text="e.g. Secretary, Captain")

    # ── Role & Barangay ──
    role           = models.CharField(max_length=20, choices=ROLE_CHOICES, default=USER)
    barangay       = models.ForeignKey(
        "barangays.Barangay",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="members",
    )

    # ── Django auth flags ──
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # ── Security & Lockout ──
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login     = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    # ── Role helpers ──
    @property
    def is_barangay_admin(self):
        return self.role == self.ADMIN

    @property
    def is_super_admin(self):
        return self.role == self.SUPERADMIN

    @property
    def is_resident(self):
        return self.role == self.USER

import uuid

class UserDevice(models.Model):
    """Tracks known browsers/devices to detect unrecognized logins."""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='devices')
    
    # Device fingerprinting
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    
    # Link to active session in Django's Session table
    session_key = models.CharField(max_length=40, null=True, blank=True)
    
    is_trusted = models.BooleanField(default=False)
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Secure token used for email verification links
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return f"{self.user.email} | {self.ip_address} | {self.user_agent[:30]}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    notification_type = models.CharField(max_length=50, default="info")
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

import hashlib

class LoginOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=64) # Hashed SHA-256
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    def is_valid(self):
        from django.utils import timezone
        return timezone.now() < self.expires_at and self.used_at is None

    @staticmethod
    def hash_code(code):
        return hashlib.sha256(code.encode()).hexdigest()

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"

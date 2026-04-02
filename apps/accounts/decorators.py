"""
Permission decorators for EasyCert role-based access control.

Roles:
  - user       → Regular resident
  - admin      → Barangay-level administrator
  - superadmin → Full platform access

Usage:
    @admin_only
    def my_admin_view(request): ...

    @approved_member_required
    def submit_cert(request): ...
"""
from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages

from apps.barangays.models import BarangayMembership


# ──────────────────────────────────────────────
# ROLE-BASED DECORATORS
# ──────────────────────────────────────────────

def user_only(view_func):
    """Only allow regular users (role='user'). Redirects admins away."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.is_barangay_admin or request.user.is_super_admin:
            return redirect("admin_dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_only(view_func):
    """Only allow barangay admins and superadmins."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not (request.user.is_barangay_admin or request.user.is_super_admin or request.user.is_staff):
            messages.error(request, "You do not have admin access.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_only_api(view_func):
    """Same as admin_only but returns JSON 403 instead of redirect (for AJAX endpoints)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)
        if not (request.user.is_barangay_admin or request.user.is_super_admin or request.user.is_staff):
            return JsonResponse({"error": "Forbidden"}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def superadmin_only(view_func):
    """Only allow super admins."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_super_admin:
            messages.error(request, "This area is restricted to super administrators.")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return wrapper


# ──────────────────────────────────────────────
# MEMBERSHIP-BASED DECORATORS
# ──────────────────────────────────────────────

def approved_member_required(view_func):
    """
    Only allow users with an approved BarangayMembership.
    Admins/superadmins bypass this check.
    Unapproved users are redirected to the membership flow.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        # Admins bypass membership check
        if request.user.is_barangay_admin or request.user.is_super_admin or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # Check for an approved membership
        has_approved = BarangayMembership.objects.filter(
            user=request.user,
            status=BarangayMembership.APPROVED,
        ).exists()

        if not has_approved:
            messages.warning(
                request,
                "You need an approved barangay membership before you can do that."
            )
            # Check if they have a pending one
            has_pending = BarangayMembership.objects.filter(
                user=request.user,
                status=BarangayMembership.PENDING,
            ).exists()
            if has_pending:
                return redirect("membership_pending")
            return redirect("select_barangay")

        return view_func(request, *args, **kwargs)
    return wrapper


def approved_member_required_api(view_func):
    """Same as approved_member_required but returns JSON for AJAX endpoints."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"ok": False, "error": "Authentication required."}, status=401)

        # Admins bypass
        if request.user.is_barangay_admin or request.user.is_super_admin or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        has_approved = BarangayMembership.objects.filter(
            user=request.user,
            status=BarangayMembership.APPROVED,
        ).exists()

        if not has_approved:
            return JsonResponse({
                "ok": False,
                "error": "You need an approved barangay membership to submit certificate requests."
            }, status=403)

        return view_func(request, *args, **kwargs)
    return wrapper

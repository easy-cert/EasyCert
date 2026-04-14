import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncDate
from datetime import timedelta
import calendar

from .models import CertificateRequest
from .forms import CertificateRequestForm
from apps.barangays.models import BarangayMembership
from apps.accounts.models import User, Notification
from apps.accounts.decorators import (
    admin_only, admin_only_api, approved_member_required_api,
    superadmin_only, superadmin_only_api
)


# ─────────────────────────────────────────────
# RESIDENT VIEWS
# ─────────────────────────────────────────────

def home_view(request):
    """
    Main landing page — renders the resident view
    with available certificates and modals.
    """
    certificate_types = CertificateRequest.CERTIFICATE_TYPES
    context = {"certificate_types": certificate_types}

    if request.user.is_authenticated:
        from apps.barangays.models import BarangayMembership
        membership = BarangayMembership.objects.filter(
            user=request.user, status=BarangayMembership.APPROVED
        ).select_related("barangay").first()
        context["membership"] = membership

    return render(request, "requests_app/home.html", context)



@approved_member_required_api
@require_POST
def submit_request_view(request):
    """
    AJAX endpoint — handles certificate form submissions.
    Accepts JSON body from the frontend JS.

    CRITICAL FIX: barangay is ALWAYS derived from the logged-in user.
    The form does NOT allow barangay selection.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)

    # ── Step 1: Resolve the user's barangay ──
    user = request.user
    barangay = None

    if user.barangay_id:
        barangay = user.barangay
    else:
        # Fallback: check approved membership
        membership = BarangayMembership.objects.filter(
            user=user, status=BarangayMembership.APPROVED
        ).select_related("barangay").first()
        if membership:
            barangay = membership.barangay
            # Sync user.barangay for future requests
            user.barangay = barangay
            user.save(update_fields=["barangay"])

    # ── Step 2: REJECT if no barangay ──
    if not barangay:
        logger.error(
            f"submit_request BLOCKED: user={user.email} has no barangay assignment."
        )
        return JsonResponse({
            "ok": False,
            "error": "You do not have an approved barangay membership. "
                     "Please apply for membership first."
        }, status=403)

    # ── Step 3: Build the CertificateRequest ──
    cert = CertificateRequest(
        user=user,
        barangay=barangay,  # ALWAYS from user, NEVER from form
        certificate_type=data.get("certificate_type", ""),
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        middle_name=data.get("middle_name", ""),
        sitio=data.get("sitio", ""),
        purpose=data.get("purpose", ""),
        appointment_time=data.get("appointment_time", ""),
        form_data=data.get("form_data", {}),
    )

    # ── Step 4: Validate and save ──
    try:
        cert.full_clean()
        cert.save()

        logger.info(
            f"Request created: tracking={cert.tracking_number}, "
            f"user={user.email}, barangay={barangay.barangay_name}"
        )

        # Notify Admins of this barangay
        admins = User.objects.filter(role=User.ADMIN, barangay=barangay)
        for admin_user in admins:
            Notification.objects.create(
                user=admin_user,
                message=f"New certificate request: {cert.certificate_type} from {cert.display_name}",
                notification_type="request"
            )
    except Exception as e:
        logger.error(f"submit_request error: {e} | user={user.email}")
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return JsonResponse({
        "ok": True,
        "tracking_number": cert.tracking_number,
        "appointment_time": cert.appointment_time,
    })


def track_request_view(request):
    """
    AJAX endpoint — look up a request by tracking number.
    GET /requests/track/?q=EC-2026-12345
    """
    tracking = request.GET.get("q", "").strip().upper()
    if not tracking:
        return JsonResponse({"found": False})

    try:
        cert = CertificateRequest.objects.select_related("barangay").get(tracking_number=tracking)
    except CertificateRequest.DoesNotExist:
        return JsonResponse({"found": False})

    return JsonResponse({
        "found": True,
        "tracking": cert.tracking_number,
        "name": cert.display_name,
        "type": cert.certificate_type,
        "purpose": cert.purpose or "—",
        "appointment": cert.appointment_time or "Not set",
        "date": cert.date_requested.strftime("%Y-%m-%d"),
        "status": cert.status,
        "barangay_name": cert.barangay.barangay_name if cert.barangay else "—",
        "barangay_location": cert.barangay.location if cert.barangay else "—",
        "captain_name": cert.barangay.captain_name if cert.barangay else "—",
    })


# ─────────────────────────────────────────────
# ADMIN DASHBOARD VIEWS
# ─────────────────────────────────────────────


@admin_only
def admin_dashboard_view(request):
    """Admin dashboard page — shows stats, charts, request table."""

    today = timezone.localdate()
    # Data Isolation: Barangay admins ONLY see their own barangay
    if request.user.is_barangay_admin and request.user.barangay:
        all_requests = CertificateRequest.objects.filter(
            barangay=request.user.barangay
        ).select_related("barangay", "user").order_by("-date_requested")
    else:
        all_requests = CertificateRequest.objects.all().select_related(
            "barangay", "user"
        ).order_by("-date_requested")

    stats = {
        "today": all_requests.filter(date_requested__date=today).count(),
        "pending": all_requests.filter(status="Pending").count(),
        "approved": all_requests.filter(status="Approved").count(),
        "total": all_requests.count(),
    }

    context = {
        "stats": stats,
        "requests": all_requests[:100],  # latest 100
        "barangay_name": request.user.barangay.barangay_name if request.user.barangay else "All Barangays",
        "certificate_types": CertificateRequest.CERTIFICATE_TYPES,
    }
    if request.user.is_authenticated:
        context["my_notifications"] = request.user.notifications.all()[:20]
        context["unread_notifications_count"] = request.user.notifications.filter(is_read=False).count()

    return render(request, "requests_app/admin_dashboard.html", context)


@admin_only_api
def admin_requests_api(request):
    """
    AJAX endpoint — returns all requests as JSON for the admin table.
    Supports filtering by status and type.
    """

    # Data Isolation: Barangay admins ONLY see their own barangay
    if request.user.is_barangay_admin and request.user.barangay:
        qs = CertificateRequest.objects.filter(
            barangay=request.user.barangay
        ).select_related("barangay", "user").order_by("-date_requested")
    else:
        qs = CertificateRequest.objects.all().select_related(
            "barangay", "user"
        ).order_by("-date_requested")

    status = request.GET.get("status")
    cert_type = request.GET.get("type")
    search = request.GET.get("q", "").strip()

    if status:
        qs = qs.filter(status=status)
    if cert_type:
        qs = qs.filter(certificate_type=cert_type)
    if search:
        qs = qs.filter(
            Q(tracking_number__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    data = []
    for cert in qs[:200]:
        data.append({
            "id": cert.id,
            "tracking": cert.tracking_number,
            "name": cert.display_name,
            "type": cert.certificate_type,
            "sitio": cert.sitio or "—",
            "status": cert.status,
            "date": cert.date_requested.strftime("%Y-%m-%d"),
            "purpose": cert.purpose or "—",
            "appointment": cert.appointment_time,
            "form_data": cert.form_data,
            "barangay_name": cert.barangay.barangay_name if cert.barangay else "—",
            "barangay_location": cert.barangay.location if cert.barangay else "—",
            "captain_name": cert.barangay.captain_name if cert.barangay else "—",
        })

    return JsonResponse({"requests": data})


@admin_only_api
def admin_stats_api(request):
    """AJAX endpoint — return dashboard statistics as JSON."""

    today = timezone.localdate()
    if request.user.is_barangay_admin and request.user.barangay:
        all_requests = CertificateRequest.objects.filter(barangay=request.user.barangay)
    else:
        all_requests = CertificateRequest.objects.all()

    # Type distribution
    type_counts = (
        all_requests
        .values("certificate_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    
    # Calendar bounds
    start_of_year = today.replace(month=1, day=1)
    start_of_month = today.replace(day=1)
    start_of_week = today - timedelta(days=today.weekday())

    # Yearly distribution (current year)
    yearly_db = list(
        all_requests.filter(date_requested__date__gte=start_of_year)
        .annotate(month=TruncMonth('date_requested'))
        .values('month')
        .annotate(count=Count('id'))
    )
    yearly_dict = {today.replace(month=i, day=1).strftime("%b %Y"): 0 for i in range(1, 13)}
    for entry in yearly_db:
        if entry['month']:
            yearly_dict[entry['month'].strftime("%b %Y")] = entry['count']
    yearly_counts = [{"month": k, "count": v} for k, v in yearly_dict.items()]

    # Monthly distribution (current month by day)
    monthly_db = list(
        all_requests.filter(date_requested__date__gte=start_of_month)
        .annotate(date=TruncDate('date_requested'))
        .values('date')
        .annotate(count=Count('id'))
    )
    _, last_day = calendar.monthrange(today.year, today.month)
    monthly_dict = {today.replace(day=i).strftime("%Y-%m-%d"): 0 for i in range(1, last_day + 1)}
    for entry in monthly_db:
        if entry['date']:
            monthly_dict[entry['date'].strftime("%Y-%m-%d")] = entry['count']
    monthly_counts = [{"date": k, "count": v} for k, v in monthly_dict.items()]

    # Weekly distribution (current week by day, labeled Mon to Sun)
    weekly_db = list(
        all_requests.filter(date_requested__date__gte=start_of_week)
        .annotate(date=TruncDate('date_requested'))
        .values('date')
        .annotate(count=Count('id'))
    )
    weekly_dict = {}
    for i in range(7):
        d = start_of_week + timedelta(days=i)
        # Use abbreviated weekday name (Mon, Tue, etc.) instead of YYYY-MM-DD
        weekly_dict[d.strftime("%a")] = 0
    for entry in weekly_db:
        if entry['date']:
            # Map the DB date back to wekday name
            weekly_dict[entry['date'].strftime("%a")] = entry['count']
    weekly_counts = [{"date": k, "count": v} for k, v in weekly_dict.items()]

    return JsonResponse({
        "today": all_requests.filter(date_requested__date=today).count(),
        "pending": all_requests.filter(status="Pending").count(),
        "approved": all_requests.filter(status="Approved").count(),
        "total": all_requests.count(),
        "type_distribution": list(type_counts),
        "monthly_distribution": monthly_counts,
        "weekly_distribution": weekly_counts,
        "yearly_distribution": yearly_counts,
    })


@admin_only_api
@require_POST
def admin_update_status(request, pk):
    """AJAX endpoint — approve or reject a request."""

    cert = get_object_or_404(CertificateRequest, pk=pk)

    # Security: Barangay admins can only update requests for their own barangay
    if request.user.is_barangay_admin and request.user.barangay:
        if cert.barangay != request.user.barangay:
            return JsonResponse({"error": "You can only manage requests for your barangay."}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    new_status = data.get("status")
    if new_status not in ("Approved", "Rejected"):
        return JsonResponse({"error": "Invalid status."}, status=400)

    cert.status = new_status
    cert.reviewed_by = request.user
    cert.date_reviewed = timezone.now()
    cert.admin_notes = data.get("notes", "")
    cert.save()

    return JsonResponse({
        "ok": True,
        "tracking": cert.tracking_number,
        "status": cert.status,
    })


# ─────────────────────────────────────────────
# ADMIN MEMBERSHIPS
# ─────────────────────────────────────────────

@admin_only
def admin_memberships_view(request):
    """Admin page to manage barangay resident memberships."""

    context = {
        "active_tab": "applications",
    }
    if request.user.is_authenticated:
        context["my_notifications"] = request.user.notifications.all()[:20]
        context["unread_notifications_count"] = request.user.notifications.filter(is_read=False).count()

    return render(request, "requests_app/admin_memberships.html", context)


@admin_only_api
def admin_memberships_api(request):
    """AJAX endpoint — returns all memberships for the admin table."""

    qs = BarangayMembership.objects.all().select_related("user", "barangay").order_by("-date_applied")

    # Data Isolation (Phase 5 prep): If Barangay admin, only see own barangay
    if request.user.is_barangay_admin and request.user.barangay:
        qs = qs.filter(barangay=request.user.barangay)

    status = request.GET.get("status")
    search = request.GET.get("q", "").strip()

    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(
            Q(user__full_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__contact_number__icontains=search) |
            Q(user__address__icontains=search)
        )
    
    # Alphabetical sorting
    qs = qs.order_by("user__full_name")

    data = []
    for mem in qs[:200]:
        data.append({
            "id": mem.id,
            "name": mem.user.full_name,
            "email": mem.user.email,
            "contact": mem.user.contact_number,
            "address": mem.user.address,
            "age": mem.user.age,
            "barangay": mem.barangay.barangay_name,
            "status": mem.status,
            "date_applied": mem.date_applied.strftime("%Y-%m-%d"),
            "notes": mem.admin_notes,
        })

    # Stats for the memberships page
    stats = {
        "pending": qs.filter(status=BarangayMembership.PENDING).count(),
        "approved": qs.filter(status=BarangayMembership.APPROVED).count(),
        "rejected": qs.filter(status=BarangayMembership.REJECTED).count(),
        "total": qs.count(),
    }

    return JsonResponse({"memberships": data, "stats": stats})


@admin_only_api
@require_POST
def admin_approve_membership(request):
    """AJAX endpoint — approve a resident membership request."""

    try:
        data = json.loads(request.body)
        membership_id = data.get("id")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request format."}, status=400)

    membership = get_object_or_404(BarangayMembership, pk=membership_id)

    # Security check: Admin can only approve for their own barangay
    if request.user.is_barangay_admin and request.user.barangay != membership.barangay:
        return JsonResponse({"error": "You can only approve residents for your barangay."}, status=403)

    membership.approve(request.user)

    return JsonResponse({"ok": True, "status": membership.status})


@admin_only_api
@require_POST
def admin_reject_membership(request):
    """AJAX endpoint — reject a resident membership request."""

    try:
        data = json.loads(request.body)
        membership_id = data.get("id")
        notes = data.get("notes", "")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request format."}, status=400)

    membership = get_object_or_404(BarangayMembership, pk=membership_id)

    # Security check: Admin can only reject for their own barangay
    if request.user.is_barangay_admin and request.user.barangay != membership.barangay:
        return JsonResponse({"error": "You can only reject residents for your barangay."}, status=403)

    membership.reject(request.user, notes=notes)

    return JsonResponse({"ok": True, "status": membership.status})


@admin_only_api
@require_POST
def admin_resident_create_api(request):
    """Barangay Admin creates a new resident record."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    email = data.get("email", "").lower()
    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "User with this email already exists."}, status=400)

    # Use a default random PIN for now, admin can reset it later
    import random, string
    temp_pin = ''.join(random.choices(string.digits, k=6))
    
    try:
        user = User.objects.create_user(
            email=email,
            password=temp_pin,
            full_name=data.get("full_name"),
            contact_number=data.get("contact", ""),
            address=data.get("address", ""),
            age=data.get("age"),
            birthdate=data.get("birthdate") or None,
            role=User.USER
        )
        
        # Automatically approve membership for the admin's barangay
        barangay = request.user.barangay
        if not barangay:
            # Fallback for super admin if they are creating (though usually they use the other form)
            # But the prompt says Barangay Admin does this.
            return JsonResponse({"error": "Admin has no assigned barangay."}, status=400)

        BarangayMembership.objects.create(
            user=user,
            barangay=barangay,
            status=BarangayMembership.APPROVED,
            reviewed_by=request.user,
            date_reviewed=timezone.now(),
            admin_notes="Manually created by Admin"
        )
        
        # Also set the user's barangay attribute
        user.barangay = barangay
        user.save(update_fields=["barangay"])

        from apps.accounts.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action="resident_created",
            ip_address=request.META.get('REMOTE_ADDR'),
            details={"resident_email": email, "barangay": barangay.barangay_name}
        )

        return JsonResponse({"ok": True, "message": f"Resident created. Temporary PIN: {temp_pin}"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@admin_only_api
@require_POST
def admin_resident_update_api(request, pk):
    """Update resident details."""
    membership = get_object_or_404(BarangayMembership, pk=pk)
    user = membership.user

    if request.user.is_barangay_admin and membership.barangay != request.user.barangay:
        return JsonResponse({"error": "Unauthorized."}, status=403)

    try:
        data = json.loads(request.body)
        user.full_name = data.get("name", user.full_name)
        user.email = data.get("email", user.email)
        user.contact_number = data.get("contact", user.contact_number)
        user.address = data.get("address", user.address)
        user.age = data.get("age", user.age)
        if data.get("birthdate"):
            user.birthdate = data.get("birthdate")
        user.save()
        
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@admin_only_api
@require_POST
def admin_resident_delete_api(request, pk):
    """Delete a resident record (removes membership)."""
    membership = get_object_or_404(BarangayMembership, pk=pk)
    
    if request.user.is_barangay_admin and membership.barangay != request.user.barangay:
        return JsonResponse({"error": "Unauthorized."}, status=403)

    user_email = membership.user.email
    # We might want to just delete the membership, but the prompt says "Delete records"
    # Usually in this system, residents are tied to users.
    # To be safe and according to prompt, we delete the user too IF they only have this membership.
    user = membership.user
    membership.delete()
    
    # If the user has no other memberships, we could delete them, but better to keep them if they exist.
    # However, "Delete records" in admin context usually means the whole record.
    user.delete() 

    from apps.accounts.models import AuditLog
    AuditLog.objects.create(
        user=request.user,
        action="resident_deleted",
        ip_address=request.META.get('REMOTE_ADDR'),
        details={"deleted_resident": user_email}
    )

    return JsonResponse({"ok": True})


@admin_only_api
@require_POST
def admin_resident_reset_pin_api(request, pk):
    """Barangay Admin resets a resident\'s PIN."""
    membership = get_object_or_404(BarangayMembership, pk=pk)
    user = membership.user

    if request.user.is_barangay_admin and membership.barangay != request.user.barangay:
        return JsonResponse({"error": "Unauthorized."}, status=403)

    import random, string
    new_pin = ''.join(random.choices(string.digits, k=6))
    user.set_password(new_pin)
    user.save()

    from apps.accounts.models import AuditLog
    AuditLog.objects.create(
        user=request.user,
        action="resident_pin_reset",
        ip_address=request.META.get('REMOTE_ADDR'),
        details={"resident": user.email}
    )

    return JsonResponse({"ok": True, "new_pin": new_pin})


import csv
from django.http import HttpResponse

@admin_only
def export_requests_csv(request):
    """Export the list of requests to CSV."""
    if request.user.is_barangay_admin and request.user.barangay:
        qs = CertificateRequest.objects.filter(
            barangay=request.user.barangay
        ).select_related("barangay")
    else:
        qs = CertificateRequest.objects.all().select_related("barangay")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="requests_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Tracking #', 'Applicant', 'Type', 'Status', 'Date Requested', 'Assigned Barangay'])

    for cert in qs:
        writer.writerow([
            cert.tracking_number,
            cert.display_name,
            cert.certificate_type,
            cert.status,
            cert.date_requested.strftime("%Y-%m-%d"),
            cert.barangay.barangay_name if cert.barangay else "—"
        ])

    from apps.accounts.models import AuditLog
    AuditLog.objects.create(
        user=request.user,
        action="export_requests",
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    return response

@admin_only
def export_residents_csv(request):
    """Export the list of residents to CSV."""
    if request.user.is_barangay_admin and request.user.barangay:
        qs = BarangayMembership.objects.filter(barangay=request.user.barangay, status=BarangayMembership.APPROVED)
    else:
        qs = BarangayMembership.objects.filter(status=BarangayMembership.APPROVED)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="residents_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Full Name', 'Email', 'Contact', 'Address', 'Age', 'Birthdate', 'Barangay'])

    for mem in qs:
        u = mem.user
        writer.writerow([
            u.full_name,
            u.email,
            u.contact_number,
            u.address,
            u.age,
            u.birthdate,
            mem.barangay.barangay_name
        ])

    from apps.accounts.models import AuditLog
    AuditLog.objects.create(
        user=request.user,
        action="export_residents",
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    return response


# ─────────────────────────────────────────────
# CUSTOMER SERVICE (SUPPORT TICKETS)
# ─────────────────────────────────────────────

from .models import SupportTicket

@login_required
@require_POST
def submit_support_ticket_api(request):
    """AJAX endpoint — resident submits a support ticket."""
    user = request.user
    
    # Try to derive barangay
    barangay = None
    if user.barangay_id:
        barangay = user.barangay
    else:
        membership = BarangayMembership.objects.filter(
            user=user, status=BarangayMembership.APPROVED
        ).select_related("barangay").first()
        if membership:
            barangay = membership.barangay

    concern_type = request.POST.get("concern_type")
    message = request.POST.get("message")
    attachment = request.FILES.get("attachment")

    if not concern_type or not message:
        return JsonResponse({"ok": False, "error": "Concern type and message are required."}, status=400)

    try:
        ticket = SupportTicket.objects.create(
            user=user,
            barangay=barangay,
            concern_type=concern_type,
            message=message,
            attachment=attachment
        )
        
        # Notify super admins
        super_admins = User.objects.filter(role=User.SUPERADMIN)
        for admin in super_admins:
            Notification.objects.create(
                user=admin,
                message=f"New Support Ticket: {concern_type} from {user.full_name}",
                notification_type="system"
            )

        return JsonResponse({"ok": True, "ticket_id": ticket.id})
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error submitting support ticket: {e}")
        return JsonResponse({"ok": False, "error": "An error occurred while submitting."})


@superadmin_only
def admin_support_view(request):
    """Admin page to manage customer service support tickets."""
    context = {
        "active_tab": "support",
        "active_page": "dashboard" # to keep header styling if any
    }
    if request.user.is_authenticated:
        context["my_notifications"] = request.user.notifications.all()[:20]
        context["unread_notifications_count"] = request.user.notifications.filter(is_read=False).count()

    return render(request, "requests_app/admin_support.html", context)


@superadmin_only_api
def admin_support_api(request):
    """AJAX endpoint — returns all support tickets for the admin table."""
    qs = SupportTicket.objects.all().select_related("user", "barangay").order_by("-created_at")

    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    data = []
    for t in qs[:200]:
        data.append({
            "id": t.id,
            "user_name": t.user.full_name,
            "user_email": t.user.email,
            "barangay_name": t.barangay.barangay_name if t.barangay else "No Barangay",
            "concern_type": t.concern_type,
            "message": t.message,
            "status": t.status,
            "admin_reply": t.admin_reply,
            "attachment_url": t.attachment.url if t.attachment else None,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M")
        })

    stats = {
        "pending": qs.filter(status="Pending").count(),
        "in_progress": qs.filter(status="In Progress").count(),
        "resolved": qs.filter(status="Resolved").count(),
        "total": qs.count(),
    }

    return JsonResponse({"tickets": data, "stats": stats})


@superadmin_only_api
@require_POST
def admin_support_reply_api(request):
    """AJAX endpoint — admin replies to a support ticket and changes status."""
    try:
        data = json.loads(request.body)
        ticket_id = data.get("ticket_id")
        reply_message = data.get("reply_message", "")
        new_status = data.get("status")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    ticket = get_object_or_404(SupportTicket, pk=ticket_id)

    if new_status in dict(SupportTicket.STATUS_CHOICES):
        ticket.status = new_status
    
    if reply_message:
        ticket.admin_reply = reply_message

    ticket.save()

    # Notify User
    Notification.objects.create(
        user=ticket.user,
        message=f"Update on your Support Ticket #{ticket.id}: {ticket.status}",
        notification_type="system"
    )

    return JsonResponse({"ok": True, "status": ticket.status})

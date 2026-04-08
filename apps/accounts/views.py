from datetime import timedelta
import random
import string
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail

from .forms import (
    RegisterForm, LoginForm, ProfileUpdateForm, PasswordChangeForm, 
    AdminRegistrationForm
)
from .decorators import user_only, approved_member_required, superadmin_only
from apps.barangays.models import Barangay, BarangayMembership
from .models import User, AuditLog, LoginOTP, UserDevice, Notification

logger = logging.getLogger(__name__)


def register_view(request):
    """Handle resident registration."""
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="apps.accounts.backends.EmailBackend")
            messages.success(request, "Account created successfully! Welcome to EasyCert.")
            return redirect("select_barangay")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """Handle email + password login, checking for concurrent sessions."""
    if request.user.is_authenticated:
        return _redirect_after_login(request.user)

    # When requesting the login page, clear any pending OTP state
    # so the user is not trapped by the OTPMiddleware.
    if request.method == "GET":
        request.session.pop("pending_otp_user_id", None)
        request.session.pop("pending_login_backend", None)
        request.session.pop("pending_next_url", None)

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            password = form.cleaned_data["password"]
            
            # Security: Check for lockout
            user_candidate = User.objects.filter(email=email).first()
            from django.utils import timezone
            from datetime import timedelta
            
            if user_candidate:
                if user_candidate.failed_login_attempts >= 5:
                    if user_candidate.last_failed_login and (timezone.now() - user_candidate.last_failed_login) < timedelta(minutes=15):
                        from .models import AuditLog
                        AuditLog.objects.create(
                            user=user_candidate,
                            action="login_failure_locked",
                            ip_address=request.META.get('REMOTE_ADDR'),
                            details={"reason": "Account locked due to 5+ failed attempts"}
                        )
                        messages.error(request, "Account temporarily locked due to multiple failed attempts. Please try again in 15 minutes.")
                        return render(request, "accounts/login.html", {"form": form})
            
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                # SUCCESS - Reset lockout
                user.failed_login_attempts = 0
                user.save(update_fields=['failed_login_attempts'])
                
                # ── OTP ENFORCEMENT ──
                from .models import UserDevice, LoginOTP, Notification, AuditLog
                from django.contrib.sessions.models import Session
                import random
                import string
                from django.core.mail import send_mail
                from django.conf import settings
                import logging

                logger = logging.getLogger(__name__)
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

                # Log the successful but incomplete (pre-OTP) login
                AuditLog.objects.create(
                    user=user,
                    action="login_step1_success",
                    ip_address=ip_address,
                    details={"user_agent": user_agent}
                )

                # Generate a secure 6-digit OTP
                otp_code = ''.join(random.choices(string.digits, k=6))
                hashed_code = LoginOTP.hash_code(otp_code)
                expires = timezone.now() + timedelta(minutes=5)
                
                # Store hashed OTP
                LoginOTP.objects.create(user=user, code=hashed_code, expires_at=expires)

                # Email Delivery
                email_sent = False
                try:
                    send_mail(
                        "Your EasyCert Login Verification Code",
                        f"Hello {user.full_name},\n\n"
                        f"A login attempt was detected for your account.\n\n"
                        f"Your verification code is: {otp_code}\n\n"
                        f"This code will expire in 5 minutes.",
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    email_sent = True
                except Exception as e:
                    logger.error(f"OTP email fail: {str(e)}")

                # Determine if this is a known device
                known_device = UserDevice.objects.filter(
                    user=user, 
                    ip_address=ip_address, 
                    user_agent=user_agent,
                    is_trusted=True
                ).exists()

                if not known_device:
                    # New Device detected! Send alert immediately.
                    try:
                        send_mail(
                            "🚨 Security Alert: New Device Login Attempt",
                            f"Hello {user.full_name},\n\n"
                            f"An unrecognized device has attempted to sign in to your EasyCert account ({user.email}).\n\n"
                            f"Location/IP: {ip_address}\n"
                            f"Browser/Device: {user_agent}\n\n"
                            "If this was not you, we highly recommend resetting your PIN immediately.\n"
                            "A one-time verification code has been generated and sent to you to proceed.",
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        logger.error(f"Security Alert email failed: {str(e)}")
                    
                    Notification.objects.create(
                        user=user,
                        message=f"Security Alert: Login attempt from an unrecognized device ({ip_address}).",
                        notification_type="security"
                    )

                Notification.objects.create(
                    user=user,
                    message=f"Your verification code is: {otp_code}. (Attempts from {ip_address})",
                    notification_type="otp"
                )

                request.session['pending_otp_user_id'] = user.id
                request.session['pending_login_backend'] = "apps.accounts.backends.EmailBackend"
                request.session['pending_next_url'] = request.GET.get("next", "")
                
                return redirect('verify_otp')
            else:
                # FAILURE - Increment lockout
                if user_candidate:
                    user_candidate.failed_login_attempts += 1
                    user_candidate.last_failed_login = timezone.now()
                    user_candidate.save(update_fields=['failed_login_attempts', 'last_failed_login'])
                    
                    if user_candidate.role == user_candidate.ADMIN:
                        from .models import LoginLog, Notification
                        import logging
                        LoginLog.objects.create(
                            email=email,
                            ip_address=request.META.get('REMOTE_ADDR'),
                            status="Failed"
                        )
                        Notification.objects.create(
                            user=user_candidate,
                            message=f"Login attempt detected from {request.META.get('REMOTE_ADDR')} (Failed)",
                            notification_type="security"
                        )
                
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def verify_otp_view(request):
    """
    OTP verification view for simultaneous logins.
    """
    user_id = request.session.get('pending_otp_user_id')
    if not user_id:
        return redirect('login')
        
    user = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "VERIFY":
            code = request.POST.get("otp_code")
            from django.contrib.sessions.models import Session
            
            hashed_input = LoginOTP.hash_code(code)
            
            # Find the latest valid OTP for this user
            otp = LoginOTP.objects.filter(user=user, code=hashed_input).last()
            
            if otp and otp.is_valid():
                # 1. Invalidate all previous sessions for security
                for device in UserDevice.objects.filter(user=user):
                    if device.session_key:
                        Session.objects.filter(session_key=device.session_key).delete()
                
                # 2. Mark OTP as used
                otp.used_at = timezone.now()
                otp.save()
                
                # 3. Log the successful verification
                AuditLog.objects.create(
                    user=user,
                    action="login_verification_success",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                if user.role == user.ADMIN:
                    from .models import LoginLog
                    LoginLog.objects.create(
                        email=user.email,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        status="Success"
                    )
                    Notification.objects.create(
                        user=user,
                        message=f"Login attempt detected from {request.META.get('REMOTE_ADDR')} (Success)",
                        notification_type="security"
                    )
                        
                # 4. Create success notification
                Notification.objects.create(
                    user=user,
                    message="New login verified. All previous sessions have been terminated for your security.",
                    notification_type="success"
                )
                        
                # 4. Perform Login
                backend = request.session.get('pending_login_backend', "apps.accounts.backends.EmailBackend")
                next_url = request.session.pop('pending_next_url', None)
                
                login(request, user, backend=backend)
                
                # 5. Register this device as trusted
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
                device, _ = UserDevice.objects.get_or_create(
                    user=user, 
                    ip_address=ip_address, 
                    user_agent=user_agent
                )
                device.session_key = request.session.session_key
                device.is_trusted = True
                device.save()

                # Cleanup session variables
                request.session.pop('pending_otp_user_id', None)
                request.session.pop('pending_login_backend', None)
                
                logger.info(f"OTP successful for user {user.email}")
                messages.success(request, "Verification successful! All other sessions were logged out.")
                
                if next_url:
                    return redirect(next_url)
                return _redirect_after_login(user)
            
            elif otp and not otp.is_valid():
                logger.warning(f"Expired OTP attempt for {user.email}")
                messages.error(request, "Your verification OTP has expired. Please try logging in again to get a new one.")
                return redirect('login')
            else:
                logger.warning(f"Invalid OTP code entered for {user.email}")
                messages.error(request, "The code you entered is incorrect. Please check your email.")
                
        elif action == "RESEND":
            import random
            import string
            from django.core.mail import send_mail
            from django.conf import settings
            
            # Delete old unexpired OTPs to prevent confusion
            LoginOTP.objects.filter(user=user).delete()

            otp_code = ''.join(random.choices(string.digits, k=6))
            hashed_code = LoginOTP.hash_code(otp_code)
            expires = timezone.now() + timedelta(minutes=5)
            
            LoginOTP.objects.create(user=user, code=hashed_code, expires_at=expires)
            
            try:
                send_mail(
                    "Your New Verification Code - EasyCert",
                    f"Hello {user.full_name},\n\n"
                    f"Here is your new verification code: {otp_code}\n\n"
                    f"This code will expire in 5 minutes.",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, "A new verification code has been sent to your email.")
            except Exception as e:
                logger.error(f"OTP resend email fail: {str(e)}")
                messages.error(request, "Failed to send email. Please try again.")
                
            return redirect('verify_otp')

        elif action == "CANCEL":
            request.session.pop('pending_otp_user_id', None)
            request.session.pop('pending_login_backend', None)
            request.session.pop('pending_next_url', None)
            messages.info(request, "Login abandoned. Your existing session remains active.")
            return redirect('login')

    return render(request, "accounts/verify_otp.html", {"user": user})

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def clear_notifications_api(request):
    """
    AJAX endpoint to clear (delete) all notifications for the current user.
    """
    request.user.notifications.all().delete()
    return JsonResponse({"status": "success", "message": "All notifications cleared."})

@login_required
@require_POST
def mark_notifications_read_api(request):
    """
    AJAX endpoint to mark unread notifications as read.
    """
    import json
    try:
        body = json.loads(request.body)
        notif_type = body.get("type")
    except:
        notif_type = request.POST.get("type")
        
    qs = request.user.notifications.filter(is_read=False)
    if notif_type:
        qs = qs.filter(notification_type=notif_type)
        
    qs.update(is_read=True)
    return JsonResponse({"status": "success", "message": "Notifications marked as read."})

@login_required
def get_notification_count_api(request):
    """
    Simple AJAX endpoint to check for current unread count.
    Provides detailed breakdown for Barangay Admins.
    """
    qs = request.user.notifications.filter(is_read=False)
    data = {"unread_count": qs.count()}
    
    if request.user.is_barangay_admin:
        data["certs_count"] = qs.filter(notification_type="request").count()
        data["members_count"] = qs.filter(notification_type="membership").count()
        
    return JsonResponse(data)


@login_required
def login_logs_api(request):
    """
    AJAX endpoint — returns login history for the admin dashboard.
    Barangay admins see logs for their barangay admins only.
    Superadmins see all logs.
    """
    from .models import LoginLog
    if not (request.user.is_barangay_admin or request.user.is_super_admin or request.user.is_staff):
        return JsonResponse({"error": "Forbidden"}, status=403)

    if request.user.is_super_admin:
        qs = LoginLog.objects.all()[:50]
    else:
        qs = LoginLog.objects.filter(email=request.user.email)[:50]
        
    logs = []
    for log in qs:
        logs.append({
            "email": log.email or "—",
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "—",
            "ip_address": log.ip_address or "—",
            "status": log.status,
        })
    return JsonResponse({"logs": logs})


def _redirect_after_login(user):
    """
    Determine where to send a user after login based on role & membership.
    """
    if user.is_super_admin or user.is_barangay_admin or user.is_staff:
        return redirect("admin_dashboard")

    membership = BarangayMembership.objects.filter(user=user).first()
    if membership:
        if membership.is_approved:
            return redirect("user_dashboard")
        else:
            return redirect("membership_pending")

    return redirect("select_barangay")


def logout_view(request):
    """Log the user out and redirect to login page."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


# ─────────────────────────────────────────────
# BARANGAY SELECTION
# ─────────────────────────────────────────────

@user_only
def select_barangay_view(request):
    """Post-login: user picks a barangay to join."""
    existing = BarangayMembership.objects.filter(
        user=request.user, status=BarangayMembership.APPROVED
    ).first()
    if existing:
        return redirect("user_dashboard")

    pending = BarangayMembership.objects.filter(
        user=request.user, status=BarangayMembership.PENDING
    ).first()
    if pending:
        return redirect("membership_pending")

    barangays = Barangay.objects.filter(is_active=True)

    if request.method == "POST":
        barangay_id = request.POST.get("barangay")
        if not barangay_id:
            messages.error(request, "Please select a barangay.")
        else:
            barangay = get_object_or_404(Barangay, pk=barangay_id, is_active=True)

            BarangayMembership.objects.filter(
                user=request.user, status=BarangayMembership.REJECTED
            ).delete()

            membership, created = BarangayMembership.objects.get_or_create(
                user=request.user,
                barangay=barangay,
                defaults={"status": BarangayMembership.PENDING},
            )
            if created:
                # Notify Admins of this barangay
                from .models import User, Notification
                admins = User.objects.filter(role=User.ADMIN, barangay=barangay)
                for admin in admins:
                    Notification.objects.create(
                        user=admin,
                        message=f"New membership application from {request.user.full_name}",
                        notification_type="membership"
                    )
                
                messages.success(
                    request,
                    f"Your request to join {barangay.barangay_name} has been submitted!"
                )
            return redirect("membership_pending")

    return render(request, "accounts/select_barangay.html", {
        "barangays": barangays,
    })


@user_only
def membership_pending_view(request):
    """Show the user their pending/rejected membership status."""
    membership = BarangayMembership.objects.filter(user=request.user).order_by("-date_applied").first()

    if not membership:
        return redirect("select_barangay")

    if membership.is_approved:
        return redirect("user_dashboard")

    return render(request, "accounts/membership_pending.html", {
        "membership": membership,
    })


# ─────────────────────────────────────────────
# USER DASHBOARD
# ─────────────────────────────────────────────

@user_only
def user_dashboard_view(request):
    """Personal dashboard for approved residents."""
    user = request.user

    membership = BarangayMembership.objects.filter(
        user=user, status=BarangayMembership.APPROVED
    ).first()
    if not membership:
        return redirect("select_barangay")

    from apps.requests_app.models import CertificateRequest
    my_requests = CertificateRequest.objects.filter(user=user).order_by("-date_requested")

    stats = {
        "total": my_requests.count(),
        "pending": my_requests.filter(status="Pending").count(),
        "approved": my_requests.filter(status="Approved").count(),
        "rejected": my_requests.filter(status="Rejected").count(),
    }

    return render(request, "accounts/user_dashboard.html", {
        "membership": membership,
        "my_requests": my_requests[:20],
        "stats": stats,
        "active_page": "dashboard",
    })


# ─────────────────────────────────────────────
# PROFILE / ACCOUNT SETTINGS
# ─────────────────────────────────────────────

@user_only
def profile_settings_view(request):
    """Profile settings page — edit personal info & change password."""
    user = request.user

    membership = BarangayMembership.objects.filter(
        user=user, status=BarangayMembership.APPROVED
    ).first()
    if not membership:
        return redirect("select_barangay")

    profile_form = ProfileUpdateForm(instance=user)
    password_form = PasswordChangeForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            profile_form = ProfileUpdateForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect("profile_settings")

        elif action == "change_password":
            password_form = PasswordChangeForm(request.POST)
            if password_form.is_valid():
                current_pw = password_form.cleaned_data["current_password"]
                new_pw = password_form.cleaned_data["new_password"]

                if not user.check_password(current_pw):
                    password_form.add_error("current_password", "Current password is incorrect.")
                else:
                    user.set_password(new_pw)
                    user.save()
                    messages.success(request, "Password changed successfully!")
                    return redirect("profile_settings")

    # Include device history for security auditing
    from .models import UserDevice
    user_devices = UserDevice.objects.filter(user=user).order_by("-last_login")[:5]

    return render(request, "accounts/profile_settings.html", {
        "membership": membership,
        "profile_form": profile_form,
        "password_form": password_form,
        "user_devices": user_devices,
        "active_page": "settings",
    })

# ─────────────────────────────────────────────
# SUPER ADMIN: BARANGAY ADMIN MANAGEMENT
# ─────────────────────────────────────────────

@superadmin_only
def superadmin_dashboard_view(request):
    """List all barangay admins and system activity."""
    admins = User.objects.filter(role=User.ADMIN).select_related('barangay').order_by('full_name')
    audit_logs = AuditLog.objects.all()[:50]
    
    return render(request, "accounts/superadmin_dashboard.html", {
        "admins": admins,
        "audit_logs": audit_logs,
        "active_page": "admin_mgmt"
    })

@superadmin_only
def register_admin_view(request):
    """Super Admin form to create new Barangay Admin accounts."""
    if request.method == "POST":
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            admin_user = form.save()
            AuditLog.objects.create(
                user=request.user,
                action="admin_created",
                ip_address=request.META.get('REMOTE_ADDR'),
                details={"created_user": admin_user.email, "barangay": admin_user.barangay.barangay_name}
            )
            messages.success(request, f"Barangay Admin account for {admin_user.full_name} created successfully!")
            return redirect("superadmin_dashboard")
    else:
        form = AdminRegistrationForm()
    
    return render(request, "accounts/admin_register.html", {"form": form})

@superadmin_only
def edit_admin_view(request, pk):
    """Edit an existing Barangay Admin account."""
    admin_user = get_object_or_404(User, pk=pk, role=User.ADMIN)
    if request.method == "POST":
        form = AdminRegistrationForm(request.POST, instance=admin_user)
        # Handle PIN change separately if provided
        new_pin = request.POST.get('pin')
        if form.is_valid():
            user = form.save(commit=False)
            if new_pin and len(new_pin) == 6:
                user.set_password(new_pin)
            user.save()
            AuditLog.objects.create(
                user=request.user,
                action="admin_updated",
                ip_address=request.META.get('REMOTE_ADDR'),
                details={"updated_user": admin_user.email}
            )
            messages.success(request, f"Account for {admin_user.full_name} updated.")
            return redirect("superadmin_dashboard")
    else:
        form = AdminRegistrationForm(instance=admin_user)
    
    return render(request, "accounts/admin_register.html", {"form": form, "edit_mode": True, "admin_user": admin_user})

@superadmin_only
def toggle_admin_active_view(request, pk):
    """Deactivate or activate an admin account."""
    admin_user = get_object_or_404(User, pk=pk, role=User.ADMIN)
    admin_user.is_active = not admin_user.is_active
    admin_user.save()
    
    status = "activated" if admin_user.is_active else "deactivated"
    AuditLog.objects.create(
        user=request.user,
        action=f"admin_{status}",
        ip_address=request.META.get('REMOTE_ADDR'),
        details={"target_user": admin_user.email}
    )
    messages.success(request, f"Account for {admin_user.full_name} has been {status}.")
    return redirect("superadmin_dashboard")

@superadmin_only
def delete_admin_view(request, pk):
    """Permanently delete an admin account."""
    admin_user = get_object_or_404(User, pk=pk, role=User.ADMIN)
    email = admin_user.email
    admin_user.delete()
    
    AuditLog.objects.create(
        user=request.user,
        action="admin_deleted",
        ip_address=request.META.get('REMOTE_ADDR'),
        details={"deleted_email": email}
    )
    messages.success(request, f"Account for {email} has been deleted.")
    return redirect("superadmin_dashboard")

@superadmin_only
def reset_admin_pin_view(request, pk):
    """Force reset a PIN for an admin."""
    admin_user = get_object_or_404(User, pk=pk, role=User.ADMIN)
    if request.method == "POST":
        new_pin = request.POST.get('new_pin')
        if new_pin and len(new_pin) == 6 and new_pin.isdigit():
            admin_user.set_password(new_pin)
            admin_user.save()
            AuditLog.objects.create(
                user=request.user,
                action="admin_pin_reset",
                ip_address=request.META.get('REMOTE_ADDR'),
                details={"target_user": admin_user.email}
            )
            messages.success(request, f"PIN for {admin_user.full_name} has been reset.")
        else:
            messages.error(request, "Invalid PIN. Must be 6 digits.")
            
    return redirect("superadmin_dashboard")


# ─────────────────────────────────────────────
# SECURITY - UNAUTHORIZED LOGIN FLOW
# ─────────────────────────────────────────────

from django.contrib.sessions.models import Session
from .models import UserDevice

def verify_new_device_view(request, token):
    """
    Landing page from the Security Email.
    Allows user to say "Yes, it was me" or "No, log them out!"
    """
    device = get_object_or_404(UserDevice, verification_token=token)
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "YES":
            device.is_trusted = True
            device.save()
            messages.success(request, "Device safely recognized. Thank you for confirming!")
            return redirect("home")
            
        elif action == "NO":
            # 1. Immediately log out the malicious session by destroying it in the database!
            if device.session_key:
                Session.objects.filter(session_key=device.session_key).delete()
            
            # 2. Prevent device from ever being trusted
            device.delete()
            
            # 3. Inform user to change their password
            messages.error(
                request, 
                "We immediately logged out the unauthorized user. Please reset your password immediately."
            )
            
            # If the current user happens to be logged in on this browser, 
            # send them straight to profile settings to change their password
            if request.user.is_authenticated:
                return redirect("profile_settings")
            return redirect("login")

    return render(request, "accounts/verify_device.html", {"device": device})

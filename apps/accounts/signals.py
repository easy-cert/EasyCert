from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import UserDevice

def get_client_ip(request):
    """Safely fetch IP address from forwarding proxies if they exist."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

@receiver(user_logged_in)
def detect_new_device_login(sender, request, user, **kwargs):
    if not request:
        return

    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    # Ensure a session exists so we can grab the key
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    # Check if this IP & User-Agent combination is known
    device, created = UserDevice.objects.get_or_create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    # Keep the active session key up to date for this browser
    device.session_key = session_key
    device.save()

    # If this is a completely new device for this user, alert them!
    if created:
        notify_user_of_new_login(request, user, device)


def notify_user_of_new_login(request, user, device):
    """
    Sends an email alert to the user. You can also hook this up to
    a dashboard notification system.
    """
    verification_url = request.build_absolute_uri(
        f"/accounts/verify-device/{device.verification_token}/"
    )
    
    subject = "Security Alert: New Login Detected"
    message = f"""
Hello {user.full_name},

Your account was just logged into from a new browser or device.

Details:
IP Address: {device.ip_address}
Browser: {device.user_agent}

Was this you?
If YES, you can ignore this email.
If NO, immediately click the link below to log out the unauthorized user and secure your account:
{verification_url}
    """
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as e:
        # Fails silently in dev if EMAIL_BACKEND is not set up
        print(f"Failed to send security email: {e}")
        pass

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

class DualSessionMiddleware:
    """
    Middleware to isolate Django Admin sessions and CSRF cookies from Frontend sessions.
    This allows a developer (or super admin) to be logged into the Django Admin
    without affecting the frontend user session (so you can test both roles simultaneously).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.session_cookie = settings.SESSION_COOKIE_NAME
        self.csrf_cookie = settings.CSRF_COOKIE_NAME

    def __call__(self, request):
        # 1. Are we in the Django Admin?
        is_admin = request.path.startswith('/admin')
        
        admin_session_key = 'admin_sessionid'
        admin_csrf_key = 'admin_csrftoken'

        # 2. INCOMING REQUEST (Translate cookies before Django processes them)
        if is_admin:
            # Give Django the Admin session so it authenticates as Super Admin
            if admin_session_key in request.COOKIES:
                request.COOKIES[self.session_cookie] = request.COOKIES[admin_session_key]
            elif self.session_cookie in request.COOKIES:
                del request.COOKIES[self.session_cookie]

            # Give Django the Admin CSRF token
            if admin_csrf_key in request.COOKIES:
                request.COOKIES[self.csrf_cookie] = request.COOKIES[admin_csrf_key]
            elif self.csrf_cookie in request.COOKIES:
                del request.COOKIES[self.csrf_cookie]

        # 3. Process Request (Views, AuthMiddleware, and SessionMiddleware run here)
        response = self.get_response(request)

        # 4. OUTGOING RESPONSE (Translate cookies back to Admin namespace)
        if is_admin:
            # Map session cookie
            if self.session_cookie in response.cookies:
                cookie_data = response.cookies[self.session_cookie]
                # Fallback to SESSION_COOKIE_AGE if max_age is not set on the morsel
                max_age = cookie_data.get('max-age') or settings.SESSION_COOKIE_AGE
                expires = cookie_data.get('expires')
                
                logger.debug(f"Middleware setting {admin_session_key} for {request.path}: max_age={max_age}")

                response.set_cookie(admin_session_key, cookie_data.value, 
                    max_age=max_age,
                    expires=expires,
                    path=cookie_data.get('path', '/'),
                    domain=cookie_data.get('domain'),
                    secure=cookie_data.get('secure') or False,
                    httponly=cookie_data.get('httponly') or True,
                    samesite=cookie_data.get('samesite', 'Lax')
                )
                del response.cookies[self.session_cookie]

            # Map CSRF cookie
            if self.csrf_cookie in response.cookies:
                cookie_data = response.cookies[self.csrf_cookie]
                response.set_cookie(admin_csrf_key, cookie_data.value, 
                    max_age=cookie_data.get('max-age'),
                    expires=cookie_data.get('expires'),
                    path=cookie_data.get('path', '/'),
                    domain=cookie_data.get('domain'),
                    secure=cookie_data.get('secure') or False,
                    httponly=cookie_data.get('httponly') or False, # CSRF usually not httponly
                    samesite=cookie_data.get('samesite', 'Lax')
                )
                del response.cookies[self.csrf_cookie]

        return response

from django.shortcuts import redirect
from django.urls import reverse

class OTPMiddleware:
    """
    Ensures that if a user is in 'pending OTP' state, they cannot access any other
    part of the site except the verification page or login page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If there's a pending OTP user ID in the session
        if 'pending_otp_user_id' in request.session:
            # Allow access ONLY to the verify_otp and login views
            allowed_urls = [
                reverse('verify_otp'),
                reverse('login'),
                '/admin/', # Optional: allow admin access if needed, or block it
            ]
            
            # Also allow API endpoints — they have their own auth decorators
            # and must return JSON, not HTML redirects
            allowed_prefixes = [
                '/api/',
                '/static/',
            ]
            
            # Check if current path is allowed
            path = request.path
            is_allowed = (
                any(path.startswith(url) for url in allowed_urls) or
                any(path.startswith(prefix) for prefix in allowed_prefixes)
            )
            
            if not is_allowed:
                # Redirect them back to verification
                return redirect('verify_otp')

        response = self.get_response(request)
        return response

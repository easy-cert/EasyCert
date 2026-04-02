from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that authenticates using
    email + password instead of the default username.
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        User = get_user_model()
        
        # Django admin passes 'username' instead of 'email'
        if email is None:
            email = kwargs.get('username')
            
        if not email:
            return None
            
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

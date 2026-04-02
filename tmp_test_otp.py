import os
import sys
import django

# Set up Django environment
sys.path.append(r'c:\Users\Glenda Agnes\Desktop\EasyCert')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'easycert_django.settings')
django.setup()

from apps.accounts.models import LoginOTP, User, UserDevice
from django.utils import timezone
from datetime import timedelta
import hashlib

def hash_code(code):
    return hashlib.sha256(code.encode()).hexdigest()

# Example: Create a hashed OTP
user = User.objects.first()
if user:
    code = "123456"
    hashed = hash_code(code)
    expires = timezone.now() + timedelta(minutes=5)
    otp = LoginOTP.objects.create(user=user, code=hashed, expires_at=expires)
    print(f"Created OTP for {user.email}: {code} (hashed: {hashed})")
    
    # Test valid
    print(f"Is valid? {otp.is_valid()}")
    
    # Test verification
    input_code = "123456"
    print(f"Verifying {input_code}: {hash_code(input_code) == otp.code}")
    
    # Cleanup
    otp.delete()
else:
    print("No user found to test.")

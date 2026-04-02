
import os
import django
import random

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'easycert_django.settings')
django.setup()

from apps.accounts.models import User, AuditLog
from apps.barangays.models import Barangay

def seed_admins():
    print("Seeding Predefined Barangay Admins...")
    
    admins = [
        ("markamancio1@hotmail.com", "Barangay Guadalupe", "111111", "Barangay Captain"),
        ("limuelforcrypto@gmail.com", "Barangay Quiot Pardo", "222222", "Barangay Secretary"),
        ("gonzagaagnus@gmail.com", "Barangay Pahina Central", "333333", "Barangay Admin Staff"),
        ("gomezclark051@gmail.com", "Barangay Cogon Pardo", "101503", "Barangay Treasurer"),
    ]
    
    for email, b_name, pin, position in admins:
        # 1. Get or create Barangay
        b, _ = Barangay.objects.get_or_create(
            barangay_name=b_name, 
            defaults={"captain_name": "Hon. Admin"}
        )
        
        # 2. Get or create User
        user, created = User.objects.get_or_create(
            email=email.lower(),
            defaults={
                "full_name": email.split('@')[0].replace('.', ' ').title(),
                "role": User.ADMIN,
                "barangay": b,
                "position": position,
                "is_staff": True,
                "is_active": True
            }
        )
        
        # 3. Set or update PIN
        user.set_password(pin)
        user.save()
        
        status = "Created" if created else "Updated"
        print(f"{status} {email} for {b_name} | PIN: {pin} | Role: {position}")
        
        # 4. Audit Log
        AuditLog.objects.create(
            action="system_seed_admin",
            details={"email": email, "barangay": b_name, "status": status}
        )

    # Also ensure a Super Admin exists
    sa_email = "contactclark20@gmail.com"
    sa, sa_created = User.objects.get_or_create(
        email=sa_email,
        defaults={
            "full_name": "System Super Admin",
            "role": User.SUPERADMIN,
            "is_staff": True,
            "is_superuser": True,
            "position": "Lead Administrator"
        }
    )
    if sa_created:
        sa.set_password("888888")
        sa.save()
        print(f"Created Super Admin: {sa_email} | PIN: 888888")

if __name__ == "__main__":
    seed_admins()
    print("Seeding Complete.")

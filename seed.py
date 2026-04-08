# seed.py — Run once to populate sample data
# Usage: python seed.py
import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "easycert_django.settings")
django.setup()

from apps.barangays.models import Barangay
from apps.accounts.models import User, AuditLog

def seed_data():
    print("Seeding Barangays...")
    # ── Barangays (4 required) ──
    barangays_data = [
        {
            "barangay_name": "Cogon Pardo",
            "location": "Cebu City",
            "captain_name": "Hon. Juan Dela Cruz",
            "contact": "09171234501",
        },
        {
            "barangay_name": "Pahina Central",
            "location": "Cebu City",
            "captain_name": "Hon. Agnus John Wilson L. Gonzaga",
            "contact": "09171234502",
        },
        {
            "barangay_name": "Guadalupe",
            "location": "Cebu City",
            "captain_name": "Hon. Mark Anthony F. Amancio",
            "contact": "09171234503",
        },
        {
            "barangay_name": "Quiot Pardo",
            "location": "Cebu City",
            "captain_name": "Hon. Limuel M. Brasona",
            "contact": "09171234504",
        },
    ]

    for data in barangays_data:
        brgy, created = Barangay.objects.get_or_create(
            barangay_name=data["barangay_name"], defaults=data
        )
        status = "CREATED" if created else "EXISTS"
        print(f"  [{status}] {brgy.barangay_name} — Captain: {brgy.captain_name}")

    print("\nSeeding Predefined Barangay Admins...")
    
    admins = [
        ("markamancio1@hotmail.com", "Guadalupe", "111111", "Barangay Captain"),
        ("limuelforcrypto@gmail.com", "Quiot Pardo", "222222", "Barangay Secretary"),
        ("gonzagaagnus@gmail.com", "Pahina Central", "333333", "Barangay Admin Staff"),
        ("gomezclark051@gmail.com", "Cogon Pardo", "444444", "Barangay Treasurer"),
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
        print(f"  [{status}] {email} for {b_name} | PIN: {pin} | Role: {position}")
        
        # 4. Audit Log
        AuditLog.objects.create(
            action="system_seed_admin",
            details={"email": email, "barangay": b_name, "status": status}
        )

    print("\nSeeding Super Admin...")
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
        print(f"  [Created] Super Admin: {sa_email} | PIN: 888888")
    else:
        print(f"  [EXISTS] Super Admin: {sa_email}")

    # Set superadmin role on all superusers
    updated = User.objects.filter(is_superuser=True).update(role=User.SUPERADMIN)
    print(f"\nUpdated {updated} superuser(s) to role=superadmin.")

    print("\nDone! Seed data loaded successfully.")

if __name__ == "__main__":
    seed_data()

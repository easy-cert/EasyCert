# seed.py — Run once to populate sample data
# Usage: python seed.py
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "easycert_django.settings")
django.setup()

from apps.barangays.models import Barangay
from apps.accounts.models import User

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

print("Creating barangays...")
for data in barangays_data:
    brgy, created = Barangay.objects.get_or_create(
        barangay_name=data["barangay_name"], defaults=data
    )
    status = "CREATED" if created else "EXISTS"
    print(f"  [{status}] {brgy.barangay_name} — Captain: {brgy.captain_name}")

# ── Set superadmin role on all superusers ──
updated = User.objects.filter(is_superuser=True).update(role="superadmin")
print(f"\nUpdated {updated} superuser(s) to role=superadmin.")

print("\nDone! Seed data loaded successfully.")

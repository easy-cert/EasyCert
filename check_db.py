import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'easycert_django.settings'
django.setup()

from apps.accounts.models import User
from apps.requests_app.models import CertificateRequest
from apps.barangays.models import Barangay, BarangayMembership

print("=== Admin Users ===")
for u in User.objects.filter(role='admin'):
    print(f"  {u.email} | barangay={u.barangay} | active={u.is_active}")

print("\n=== Super Admins ===")
for u in User.objects.filter(role='superadmin'):
    print(f"  {u.email}")

print(f"\n=== Stats ===")
print(f"Total requests: {CertificateRequest.objects.count()}")
print(f"Barangays: {list(Barangay.objects.values_list('barangay_name', flat=True))}")

print("\n=== Requests by barangay ===")
for req in CertificateRequest.objects.select_related('barangay').all():
    brgy = req.barangay.barangay_name if req.barangay else "NULL"
    print(f"  {req.tracking_number} | {req.certificate_type} | {req.status} | barangay={brgy}")

print("\n=== All Users ===")
for u in User.objects.all():
    print(f"  {u.email} | role={u.role} | barangay={u.barangay}")

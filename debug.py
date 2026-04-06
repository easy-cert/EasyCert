import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "easycert_django.settings")
django.setup()

from apps.accounts.models import User
from apps.requests_app.models import CertificateRequest

certs = CertificateRequest.objects.all()
print(f"Total certs in DB: {certs.count()}")

data = []
for cert in certs[:200]:
    try:
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
            "barangay_name": cert.barangay.barangay_name if cert.barangay else "POBLACION",
            "barangay_location": cert.barangay.location if cert.barangay else "CEBU CITY • PHILIPPINES",
            "captain_name": cert.barangay.captain_name if cert.barangay else "Hon. Roberto L. Garcia",
        })
    except Exception as e:
        print(f"Error on cert {cert.id}: {e}")

print(f"Successfully processed {len(data)} certs.")

"""
Migration: Make CertificateRequest.barangay non-nullable.

Strategy:
1. Data migration: Fix any existing requests that have NULL barangay
   by deriving from user.barangay or approved membership.
2. Schema migration: Alter field to be non-null CASCADE.
"""

from django.db import migrations, models
import django.db.models.deletion


def fix_orphaned_requests(apps, schema_editor):
    """
    Ensure every CertificateRequest has a barangay before changing the column to NOT NULL.
    """
    CertificateRequest = apps.get_model("requests_app", "CertificateRequest")
    BarangayMembership = apps.get_model("barangays", "BarangayMembership")
    Barangay = apps.get_model("barangays", "Barangay")

    orphans = CertificateRequest.objects.filter(barangay__isnull=True)
    fixed = 0
    deleted = 0

    for req in orphans:
        assigned = False

        # Try 1: Use the user's barangay FK
        if req.user and req.user.barangay_id:
            req.barangay_id = req.user.barangay_id
            req.save(update_fields=["barangay"])
            assigned = True
            fixed += 1

        # Try 2: Look up the user's approved membership
        if not assigned and req.user:
            membership = BarangayMembership.objects.filter(
                user=req.user, status="approved"
            ).first()
            if membership:
                req.barangay = membership.barangay
                req.save(update_fields=["barangay"])
                assigned = True
                fixed += 1

        # Try 3: If still unassigned, delete the orphaned request
        # (these are data-integrity failures from the bug)
        if not assigned:
            req.delete()
            deleted += 1

    if fixed or deleted:
        print(f"\n  [fix_orphaned_requests] Fixed {fixed}, deleted {deleted} orphaned requests.")


class Migration(migrations.Migration):

    dependencies = [
        ("requests_app", "0001_initial"),
        ("barangays", "0001_initial"),
    ]

    operations = [
        # Step 1: Fix data first
        migrations.RunPython(
            fix_orphaned_requests,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 2: Alter the field to non-nullable CASCADE
        migrations.AlterField(
            model_name="certificaterequest",
            name="barangay",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="certificate_requests",
                to="barangays.barangay",
            ),
        ),
    ]

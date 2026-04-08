"""
Management command: verify_barangay_integrity

Checks the database for:
1. CertificateRequests without a barangay
2. Users without a barangay who have submitted requests
3. Cross-barangay data leakage
4. Mismatches between user.barangay and request.barangay

Usage:
    python manage.py verify_barangay_integrity
    python manage.py verify_barangay_integrity --fix
"""

from django.core.management.base import BaseCommand
from apps.requests_app.models import CertificateRequest
from apps.accounts.models import User
from apps.barangays.models import Barangay, BarangayMembership


class Command(BaseCommand):
    help = "Verify barangay data integrity in all CertificateRequests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Attempt to auto-fix issues (assign barangay from user membership).",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        issues = 0

        self.stdout.write(self.style.HTTP_INFO("\n=== BARANGAY INTEGRITY CHECK ===\n"))

        # 1. Check for requests without a barangay
        orphaned = CertificateRequest.objects.filter(barangay__isnull=True)
        if orphaned.exists():
            self.stdout.write(self.style.ERROR(
                f"✗ {orphaned.count()} request(s) have NO barangay assigned!"
            ))
            for req in orphaned:
                self.stdout.write(f"  - {req.tracking_number} | user={req.user} | barangay=None")
                if fix and req.user:
                    # Try to fix from membership
                    if req.user.barangay:
                        req.barangay = req.user.barangay
                        req.save(update_fields=["barangay"])
                        self.stdout.write(self.style.SUCCESS(f"    → Fixed: assigned {req.user.barangay}"))
                    else:
                        mem = BarangayMembership.objects.filter(
                            user=req.user, status=BarangayMembership.APPROVED
                        ).first()
                        if mem:
                            req.barangay = mem.barangay
                            req.save(update_fields=["barangay"])
                            self.stdout.write(self.style.SUCCESS(f"    → Fixed from membership: {mem.barangay}"))
                        else:
                            self.stdout.write(self.style.WARNING("    → Cannot fix: user has no approved membership"))
            issues += orphaned.count()
        else:
            self.stdout.write(self.style.SUCCESS("✓ All requests have a barangay assigned."))

        # 2. Check for users without barangay who have requests
        users_no_brgy = User.objects.filter(
            barangay__isnull=True,
            certificate_requests__isnull=False,
        ).distinct()
        if users_no_brgy.exists():
            self.stdout.write(self.style.WARNING(
                f"\n⚠ {users_no_brgy.count()} user(s) have requests but no barangay on their profile:"
            ))
            for u in users_no_brgy:
                count = u.certificate_requests.count()
                self.stdout.write(f"  - {u.email} ({count} requests)")
                if fix:
                    mem = BarangayMembership.objects.filter(
                        user=u, status=BarangayMembership.APPROVED
                    ).first()
                    if mem:
                        u.barangay = mem.barangay
                        u.save(update_fields=["barangay"])
                        self.stdout.write(self.style.SUCCESS(f"    → Fixed: set user.barangay = {mem.barangay}"))
            issues += users_no_brgy.count()
        else:
            self.stdout.write(self.style.SUCCESS("✓ All users with requests have a barangay."))

        # 3. Check for request.barangay != user.barangay mismatches
        mismatched = 0
        for req in CertificateRequest.objects.select_related("user", "barangay").exclude(user__isnull=True):
            if req.user.barangay_id and req.barangay_id != req.user.barangay_id:
                mismatched += 1
                if mismatched <= 10:
                    self.stdout.write(self.style.WARNING(
                        f"  ⚠ Mismatch: {req.tracking_number} — "
                        f"request.barangay={req.barangay} vs user.barangay={req.user.barangay}"
                    ))
        if mismatched:
            self.stdout.write(self.style.WARNING(
                f"\n⚠ {mismatched} request(s) have mismatched barangay between request and user."
            ))
            issues += mismatched
        else:
            self.stdout.write(self.style.SUCCESS("✓ No barangay mismatches between requests and users."))

        # 4. Admin visibility check
        self.stdout.write(self.style.HTTP_INFO("\n── Admin Visibility Summary ──"))
        for brgy in Barangay.objects.all():
            req_count = CertificateRequest.objects.filter(barangay=brgy).count()
            admin_count = User.objects.filter(role=User.ADMIN, barangay=brgy).count()
            self.stdout.write(
                f"  {brgy.barangay_name}: {req_count} requests, {admin_count} admin(s)"
            )

        # Summary
        self.stdout.write(self.style.HTTP_INFO("\n=== SUMMARY ==="))
        if issues:
            self.stdout.write(self.style.ERROR(f"Found {issues} issue(s)."))
            if not fix:
                self.stdout.write("Run with --fix to attempt auto-repair.")
        else:
            self.stdout.write(self.style.SUCCESS("All checks passed! ✓"))

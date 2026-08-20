from datetime import datetime
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from src.core import models


class FixDebtDomainCommandTests(TestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(
            username="domain_owner",
            password="pass123",
        )
        self.branch = models.Branch.objects.create(
            name="Domain Branch",
            owner=self.owner,
        )

    def _create_debt(self, *, name, added_at, domain=None):
        debt = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name=name,
            domain=domain,
            amount=Decimal("100.00"),
            remaining_amount=Decimal("100.00"),
            direction="WE_GAVE",
        )
        models.Debt.all_objects.filter(pk=debt.pk).update(
            added_at=added_at,
            updated_at=added_at,
        )
        debt.refresh_from_db()
        return debt

    def test_dry_run_reports_without_updating(self):
        debt = self._create_debt(
            name="March Debt",
            added_at=timezone.make_aware(
                datetime(2026, 3, 15, 12, 0, 0),
                timezone.get_current_timezone(),
            ),
        )

        stdout = StringIO()
        call_command(
            "fix_debt_domain",
            "--start-date",
            "2026-03-01",
            "--end-date",
            "2026-03-31",
            "--domain",
            models.Debt.DOMAIN_ACCESSORY,
            "--dry-run",
            stdout=stdout,
        )

        debt.refresh_from_db()
        self.assertIsNone(debt.domain)
        self.assertIn("Dry-run: 1 ta qarz", stdout.getvalue())

    def test_command_updates_only_non_deleted_debts_in_range(self):
        in_range = self._create_debt(
            name="In Range",
            added_at=timezone.make_aware(
                datetime(2026, 3, 20, 10, 0, 0),
                timezone.get_current_timezone(),
            ),
        )
        already_matching = self._create_debt(
            name="Already Accessory",
            added_at=timezone.make_aware(
                datetime(2026, 3, 21, 10, 0, 0),
                timezone.get_current_timezone(),
            ),
            domain=models.Debt.DOMAIN_ACCESSORY,
        )
        out_of_range = self._create_debt(
            name="April Debt",
            added_at=timezone.make_aware(
                datetime(2026, 4, 2, 10, 0, 0),
                timezone.get_current_timezone(),
            ),
        )
        deleted_debt = self._create_debt(
            name="Deleted Debt",
            added_at=timezone.make_aware(
                datetime(2026, 3, 22, 10, 0, 0),
                timezone.get_current_timezone(),
            ),
        )
        deleted_debt.delete()

        stdout = StringIO()
        call_command(
            "fix_debt_domain",
            "--start-date",
            "2026-03-01",
            "--end-date",
            "2026-03-31",
            "--domain",
            models.Debt.DOMAIN_ACCESSORY,
            stdout=stdout,
        )

        in_range.refresh_from_db()
        already_matching.refresh_from_db()
        out_of_range.refresh_from_db()
        deleted_debt.refresh_from_db()

        self.assertEqual(in_range.domain, models.Debt.DOMAIN_ACCESSORY)
        self.assertEqual(already_matching.domain, models.Debt.DOMAIN_ACCESSORY)
        self.assertIsNone(out_of_range.domain)
        self.assertIsNone(deleted_debt.domain)
        self.assertIn("Yangilandi: 1 ta qarz", stdout.getvalue())

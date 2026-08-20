from datetime import date, datetime
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from src.core import models


def _aware_dt(year, month, day, hour=10):
    return timezone.make_aware(
        datetime(year, month, day, hour, 0, 0),
        timezone.get_current_timezone(),
    )


class DebtMaintenanceCommandBase(TestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(
            username=f"debt_cmd_owner_{self.__class__.__name__}",
            password="pass123",
        )
        self.branch = models.Branch.objects.create(
            name=f"Debt Cmd Branch {self.__class__.__name__}",
            owner=self.owner,
        )

    def _set_added_at(self, instance, dt):
        instance.__class__.all_objects.filter(pk=instance.pk).update(
            added_at=dt,
            updated_at=dt,
        )
        instance.refresh_from_db()

    def _create_debt(self, *, name, amount, added_at):
        debt = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.owner,
            f_name=name,
            amount=Decimal(amount),
            remaining_amount=Decimal(amount),
            direction="WE_GAVE",
        )
        self._set_added_at(debt, added_at)
        return debt

    def _create_payment(self, *, debt, amount, added_at):
        payment = models.DebtPayment.objects.create(
            debt=debt,
            amount=Decimal(amount),
            remaining_balance=Decimal("0.00"),
            paid_by=self.owner,
        )
        self._set_added_at(payment, added_at)
        return payment

    def _run_command(self, command_name, *args):
        stdout = StringIO()
        call_command(command_name, *args, stdout=stdout)
        return stdout.getvalue()


class RebuildDebtSnapshotsCommandTests(DebtMaintenanceCommandBase):
    def test_command_is_safe_no_op_when_no_snapshot_exists(self):
        debt = self._create_debt(
            name="Snapshot Missing Debt",
            amount="100.00",
            added_at=_aware_dt(2026, 3, 5),
        )
        self._create_payment(
            debt=debt,
            amount="50.00",
            added_at=_aware_dt(2026, 3, 20),
        )
        month_start = date(2026, 3, 1)

        for _ in range(3):
            output = self._run_command("rebuild_debt_snapshots", "--month", "2026-03", "--force")
            snapshots = models.DebtMonthlySnapshot.objects.filter(
                debt=debt,
                month=month_start,
            )
            self.assertEqual(snapshots.count(), 0)
            self.assertIn("Snapshot yaratiladi: 0", output)
            self.assertIn("Debt adjustment apply: 0", output)

    def test_existing_snapshot_is_left_untouched(self):
        debt = self._create_debt(
            name="Snapshot Existing Debt",
            amount="100.00",
            added_at=_aware_dt(2026, 3, 7),
        )
        month_start = date(2026, 3, 1)

        first_snapshot = models.DebtMonthlySnapshot.objects.create(
            debt=debt,
            branch=debt.branch,
            month=month_start,
            remaining_amount=Decimal("100.00"),
            total_paid_until_month=Decimal("0.00"),
            direction=debt.direction,
            f_name=debt.f_name,
            note=debt.note,
            created_by=debt.created_by,
            original_created_at=debt.added_at,
        )

        for _ in range(3):
            output = self._run_command("rebuild_debt_snapshots", "--month", "2026-03", "--no-dry-run")
            snapshots = models.DebtMonthlySnapshot.objects.filter(debt=debt, month=month_start)
            self.assertEqual(snapshots.count(), 1)
            self.assertEqual(snapshots.get().id, first_snapshot.id)
            self.assertIn("Snapshot yaratiladi: 0", output)

    def test_force_does_not_delete_existing_snapshot(self):
        debt = self._create_debt(
            name="Snapshot Force Debt",
            amount="120.00",
            added_at=_aware_dt(2026, 3, 3),
        )
        self._create_payment(
            debt=debt,
            amount="20.00",
            added_at=_aware_dt(2026, 3, 15),
        )
        month_start = date(2026, 3, 1)

        stale_snapshot = models.DebtMonthlySnapshot.objects.create(
            debt=debt,
            branch=debt.branch,
            month=month_start,
            remaining_amount=Decimal("120.00"),
            total_paid_until_month=Decimal("0.00"),
            direction=debt.direction,
            f_name=debt.f_name,
            note=debt.note,
            created_by=debt.created_by,
            original_created_at=debt.added_at,
        )

        first_id = stale_snapshot.id
        for _ in range(3):
            output = self._run_command("rebuild_debt_snapshots", "--month", "2026-03", "--force")
            snapshots = models.DebtMonthlySnapshot.objects.filter(debt=debt, month=month_start)
            self.assertEqual(snapshots.count(), 1)
            snapshot = snapshots.get()
            self.assertEqual(snapshot.id, first_id)
            self.assertEqual(snapshot.total_paid_until_month, Decimal("0.00"))
            self.assertEqual(snapshot.remaining_amount, Decimal("120.00"))
            self.assertIn("Snapshot o‘chiriladi: 0", output)


class FixDebtClosedAtCommandTests(DebtMaintenanceCommandBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_closed_at_column()

    @classmethod
    def _ensure_closed_at_column(cls):
        table_name = connection.ops.quote_name(models.Debt._meta.db_table)
        with connection.cursor() as cursor:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS closed_at timestamp with time zone NULL"
            )

    def _set_debt_closed_at(self, debt, closed_at):
        table_name = connection.ops.quote_name(models.Debt._meta.db_table)
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table_name} SET closed_at = %s WHERE id = %s",
                [closed_at, debt.id],
            )

    def _get_debt_closed_at(self, debt):
        table_name = connection.ops.quote_name(models.Debt._meta.db_table)
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT closed_at FROM {table_name} WHERE id = %s",
                [debt.id],
            )
            row = cursor.fetchone()
        return row[0] if row else None

    def test_fully_closed_debt_sets_closed_at(self):
        debt = self._create_debt(
            name="Fully Closed",
            amount="100.00",
            added_at=_aware_dt(2026, 3, 1),
        )
        self._create_payment(debt=debt, amount="40.00", added_at=_aware_dt(2026, 3, 10))
        final_payment = self._create_payment(debt=debt, amount="60.00", added_at=_aware_dt(2026, 4, 4))

        outputs = []
        for _ in range(3):
            outputs.append(self._run_command("fix_debt_closed_at", "--month", "2026-04", "--force"))
            self.assertEqual(self._get_debt_closed_at(debt), final_payment.added_at)

        self.assertIn("closed_at yangilanadi: 1", outputs[0])
        self.assertIn("closed_at yangilanadi: 0", outputs[1])
        self.assertIn("closed_at yangilanadi: 0", outputs[2])

    def test_partial_closed_debt_is_skipped(self):
        debt = self._create_debt(
            name="Partial Closed",
            amount="100.00",
            added_at=_aware_dt(2026, 4, 1),
        )
        self._create_payment(debt=debt, amount="35.00", added_at=_aware_dt(2026, 4, 6))

        for _ in range(3):
            output = self._run_command("fix_debt_closed_at", "--month", "2026-04", "--force")
            self.assertIsNone(self._get_debt_closed_at(debt))
            self.assertIn("Yopilgan debt topildi: 0", output)
            self.assertIn("closed_at yangilanadi: 0", output)

    def test_already_correct_closed_at_is_not_updated(self):
        debt = self._create_debt(
            name="Already Correct",
            amount="90.00",
            added_at=_aware_dt(2026, 4, 1),
        )
        payment = self._create_payment(debt=debt, amount="90.00", added_at=_aware_dt(2026, 4, 8))
        self._set_debt_closed_at(debt, payment.added_at)

        for _ in range(3):
            output = self._run_command("fix_debt_closed_at", "--month", "2026-04", "--force")
            self.assertEqual(self._get_debt_closed_at(debt), payment.added_at)
            self.assertIn("Yopilgan debt topildi: 1", output)
            self.assertIn("closed_at yangilanadi: 0", output)

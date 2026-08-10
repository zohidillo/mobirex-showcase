import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.db import connections
from django.test import TransactionTestCase
from django.utils import timezone

from src.core import models
from src.services.month_closing import MonthClosingService


class MonthClosingRaceConditionTests(TransactionTestCase):
    def setUp(self):
        self.owner = models.User.objects.create_user(
            username="race_owner",
            password="pass123",
        )
        self.branch = models.Branch.objects.create(
            name="Race Branch",
            owner=self.owner,
        )
        self.phone_category = models.PhoneCategory.objects.create(name="Smartphones")
        self.current_month = timezone.localdate().replace(day=1)
        self.reference_time = timezone.make_aware(
            datetime(self.current_month.year, self.current_month.month, 1, 0, 1, 0),
            timezone.get_current_timezone(),
        )
        self.period = MonthClosingService.resolve_period(self.reference_time)
        self.previous_month_dt = timezone.make_aware(
            datetime(
                self.period["closing_month"].year,
                self.period["closing_month"].month,
                15,
                12,
                0,
                0,
            ),
            timezone.get_current_timezone(),
        )

        phone = models.Phone.objects.create(
            name="Phone",
            category=self.phone_category,
            branch=self.branch,
            imei="RACE-IMEI-001",
            storage="128",
            color="Black",
            from_by="Supplier",
            cost_price=Decimal("500.00"),
            added_by=self.owner,
        )
        models.Phone.all_objects.filter(pk=phone.pk).update(
            added_at=self.previous_month_dt,
            updated_at=self.previous_month_dt,
        )

    def _run_close_branch(self):
        try:
            branch = models.Branch.objects.get(pk=self.branch.pk)
            return MonthClosingService.close_branch(
                branch=branch,
                closing_month=self.period["closing_month"],
                batch_size=1,
            )
        finally:
            connections.close_all()

    def test_parallel_close_does_not_duplicate_snapshot_execution(self):
        started_event = threading.Event()
        allow_continue_event = threading.Event()
        call_count = {"value": 0}
        counter_lock = threading.Lock()
        original_calculate = MonthClosingService._calculate_snapshot_payload

        def controlled_calculate(*args, **kwargs):
            with counter_lock:
                call_count["value"] += 1
                call_number = call_count["value"]

            if call_number == 1:
                started_event.set()
                if not allow_continue_event.wait(timeout=5):
                    raise AssertionError("Timed out waiting to resume month closing")

            return original_calculate(*args, **kwargs)

        with patch.object(
            MonthClosingService,
            "_calculate_snapshot_payload",
            side_effect=controlled_calculate,
        ):
            with ThreadPoolExecutor(max_workers=2) as executor:
                first_future = executor.submit(self._run_close_branch)
                self.assertTrue(started_event.wait(timeout=5))

                second_future = executor.submit(self._run_close_branch)
                second_result = second_future.result(timeout=5)

                allow_continue_event.set()
                first_result = first_future.result(timeout=5)

        self.assertFalse(first_result.skipped)
        self.assertEqual(first_result.snapshot_action, "created")
        self.assertTrue(second_result.skipped)
        self.assertEqual(second_result.snapshot_action, "skipped")
        self.assertEqual(call_count["value"], 1)
        self.assertEqual(
            models.MonthClosingRecord.objects.filter(
                branch=self.branch,
                month=self.period["closing_month"],
                status=models.MonthClosingRecord.STATUS_COMPLETED,
            ).count(),
            1,
        )
        self.assertEqual(
            models.DashboardSnapshot.objects.filter(
                branch=self.branch,
                month=self.period["closing_month"],
            ).count(),
            1,
        )
        phone = models.Phone.objects.get(pk=models.Phone.objects.get(imei="RACE-IMEI-001").pk)
        self.assertFalse(phone.is_sold)

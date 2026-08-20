from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from src.core.tasks.month_closing import run_month_close_task, run_month_closing
from src.services.month_closing.service import BranchMonthClosingResult


class MonthClosingTaskTests(SimpleTestCase):
    def test_run_month_close_task_uses_wrapper_service(self):
        fake_result = BranchMonthClosingResult(
            branch_id=7,
            branch_name="Main Branch",
            month=date(2026, 3, 1),
            dry_run=False,
            snapshot_action="created",
        )

        with patch(
            "src.core.tasks.month_closing.MonthCloseService.close_month",
            return_value=[fake_result],
        ) as close_month:
            payload = run_month_close_task()

        close_month.assert_called_once_with(dry_run=False)
        self.assertEqual(
            payload,
            [
                {
                    "branch_id": 7,
                    "month": "2026-03-01",
                    "skipped": False,
                    "snapshot_action": "created",
                    "phones_closed": 0,
                    "phones_recreated": 0,
                    "accessories_processed": 0,
                    "error": None,
                }
            ],
        )

    def test_legacy_task_name_uses_same_runner(self):
        with patch(
            "src.core.tasks.month_closing._run_month_close",
            return_value=[{"branch_id": 99}],
        ) as runner:
            payload = run_month_closing()

        runner.assert_called_once_with()
        self.assertEqual(payload, [{"branch_id": 99}])

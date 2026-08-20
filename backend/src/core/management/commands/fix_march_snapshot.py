from datetime import date, datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from src.core import models
from src.services.dashboard import DashboardService


DEFAULT_REPAIR_MONTH = date(2026, 3, 1)


def _parse_month(value):
    try:
        return datetime.strptime(value, "%Y-%m").date().replace(day=1)
    except ValueError as exc:
        raise CommandError("--month qiymati YYYY-MM formatida bo‘lishi kerak.") from exc


class Command(BaseCommand):
    help = (
        "2026-03 dashboard snapshotini eski close_month telefon ko‘chirishlarini "
        "hisobga olib xavfsiz qayta quradi."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=_parse_month,
            default=DEFAULT_REPAIR_MONTH,
            help="Tuzatiladigan oy (default: 2026-03).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Snapshotni hisoblaydi, lekin bazaga yozmaydi.",
        )
        parser.add_argument(
            "--branch-id",
            type=int,
            help="Faqat bitta filialni qayta quradi.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="2026-03 dan boshqa oy uchun ham repair commandni ishlatishga ruxsat beradi.",
        )

    def _persist_snapshot(self, *, branch, month, payload):
        snapshot, created = models.DashboardSnapshot.objects.update_or_create(
            branch=branch,
            month=month,
            defaults={
                "dashboard_data": payload["dashboard_data"],
                "phone_data": payload["phone_data"],
                "accessory_data": payload["accessory_data"],
                "debt_data": payload["debt_data"],
                "expense_data": payload["expense_data"],
                "salary_data": payload["salary_data"],
                "capital_data": payload["capital_data"],
                "is_locked": True,
            },
        )
        return snapshot, created

    def handle(self, *args, **options):
        month = options["month"]
        dry_run = bool(options["dry_run"])
        branch_id = options.get("branch_id")
        force = bool(options["force"])

        if month != DEFAULT_REPAIR_MONTH and not force:
            raise CommandError(
                "Bu one-time repair default bo‘yicha faqat 2026-03 uchun ruxsat etiladi. "
                "Boshqa oy uchun --force qo‘shing."
            )

        branches_qs = models.Branch.objects.order_by("id")
        if branch_id is not None:
            branches_qs = branches_qs.filter(pk=branch_id)
        branches = list(branches_qs)

        if branch_id is not None and not branches:
            raise CommandError(f"Branch #{branch_id} topilmadi.")

        self.stdout.write(f"Repair month: {month.isoformat()}")
        self.stdout.write(f"Dry-run: {'yes' if dry_run else 'no'}")
        self.stdout.write(
            "Accessory repair: skipped (no reliable old close_month marker was found)."
        )

        processed = 0
        created_count = 0
        updated_count = 0
        errors = 0
        detected_total = 0
        excluded_total = 0

        for branch in branches:
            processed += 1
            snapshot_exists = models.DashboardSnapshot.objects.filter(
                branch=branch,
                month=month,
            ).exists()

            try:
                payload, repair_summary = DashboardService.build_month_snapshot_with_old_close_month_repair(
                    branch,
                    month,
                )
                detected_total += repair_summary["recreated_phones_detected"]
                excluded_total += repair_summary["artificial_sales_excluded"]

                if dry_run:
                    action = "would_update" if snapshot_exists else "would_create"
                else:
                    with transaction.atomic():
                        _, created = self._persist_snapshot(
                            branch=branch,
                            month=month,
                            payload=payload,
                        )
                    action = "created" if created else "updated"

                if action in {"created", "would_create"}:
                    created_count += 1
                else:
                    updated_count += 1

                self.stdout.write(
                    (
                        f"Branch #{branch.id} {branch.name} | detected="
                        f"{repair_summary['recreated_phones_detected']} | excluded_sales="
                        f"{repair_summary['artificial_sales_excluded']} | snapshot={action}"
                    )
                )
            except Exception as exc:
                errors += 1
                self.stderr.write(
                    f"Branch #{branch.id} {branch.name} failed: {exc}"
                )

        self.stdout.write(f"Branches processed: {processed}")
        self.stdout.write(f"Recreated phones detected: {detected_total}")
        self.stdout.write(f"Artificial phone sales excluded: {excluded_total}")
        self.stdout.write(
            f"Snapshots {'would be ' if dry_run else ''}created: {created_count}"
        )
        self.stdout.write(
            f"Snapshots {'would be ' if dry_run else ''}updated: {updated_count}"
        )
        self.stdout.write(f"Errors: {errors}")

from argparse import BooleanOptionalAction

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Debt snapshot qayta hisoblash o‘chirilgan. Command xavfsiz no-op rejimda ishlaydi."

    def add_arguments(self, parser):
        parser.add_argument("--month", type=str)
        parser.add_argument("--from", dest="from_month", type=str)
        parser.add_argument("--to", dest="to_month", type=str)
        parser.add_argument(
            "--dry-run",
            action=BooleanOptionalAction,
            default=True,
        )
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        self.stdout.write("Debt snapshot logikasi o‘chirilgan.")
        self.stdout.write("Snapshot o‘chiriladi: 0")
        self.stdout.write("Snapshot yaratiladi: 0")
        self.stdout.write("Debt adjustment apply: 0")
        self.stdout.write(self.style.WARNING("Hech qanday debt ma’lumoti o‘zgartirilmadi."))

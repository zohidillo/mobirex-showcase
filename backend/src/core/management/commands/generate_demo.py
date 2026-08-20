"""Generate demo data for Google Play / App Store review.

Idempotent. Branch-scoped. Uses existing service layer for business logic.

Usage:
    python manage.py generate_demo
    python manage.py generate_demo --force
    python manage.py generate_demo --force --months 4

`--months N` builds an N-month trading history ending with the current month
(the current month is generated only up to today, never into the future).
`--months 1` is the default and keeps the original single-month behaviour.

WHY close_month IS NEVER CALLED HERE
------------------------------------
MonthClosingService._rollover_phones / _rollover_accessories recreate next
month's rows with `Model.objects.create(...)` and never set `added_at`. The
field is `auto_now_add`, so Django stamps it with the moment the close runs —
the LAST day of the month being closed, not the first day of the next month.
The old `src/services/phone/month_close.py` corrected this with an explicit
`.update(added_at=next_month_start_dt)`; the newer service dropped that line.
Confirmed in production: the 2026-04-30 close created 118 phones dated April.

Calling close_month here would therefore drop rolled-over stock into the wrong
month and produce exactly the anomaly visible in production today (a negative
capital balance in a month that holds no inventory). So each month is generated
directly instead. Unsold phones simply stay unsold and visible — for a demo
that reads correctly: the shop has stock it has not sold yet.

Fixing the rollover bug is a separate task; this command must not depend on it.

HOW DATES ARE SET
-----------------
No create-service accepts a timestamp: `added_at` is `auto_now_add` and every
service resolves the capital month from `timezone.localtime()` / `timezone.now()`.
So each service call is made under `_frozen_clock(target_dt)`, which patches
`django.utils.timezone.now` for the duration of the call. That keeps ALL
business logic inside the service layer while routing capital to the right
month, and `added_at` / `sold_at` are additionally pinned with an explicit
`.update()` right after the call.
"""

from __future__ import annotations

import random
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from src.core.models import (
    Accessory,
    AccessoryCapital,
    AccessoryCategory,
    AccessorySale,
    Branch,
    BranchUser,
    DashboardSnapshot,
    Debt,
    DebtMonthlySnapshot,
    DebtPayment,
    Expense,
    ExtraProfit,
    Journal,
    MonthClosingRecord,
    Phone,
    PhoneCapital,
    PhoneCategory,
    Salary,
    User,
)
from src.services.accessory.create import AccessoryCreateService
from src.services.accessory.sell import AccessorySellService
from src.services.capital import CapitalService, PhoneCapitalService
from src.services.debt.create import DebtCreateService
from src.services.debt.payment import DebtPaymentService
from src.services.expense.create import ExpenseCreateService
from src.services.extra_profit.create import ExtraProfitCreateService
from src.services.phone.create import PhoneCreateService
from src.services.phone.sell import PhoneSellService
from src.services.salary.create import SalaryCreateService


DEMO_PASSWORD = "CHANGE_ME_DEMO_PASSWORD"
DEMO_PIN = "1234"
DEMO_BRANCH_NAME = "Demo Market"
# Pinned so `--force` keeps the demo on the same branch id. Without this every
# rerun deletes the branch and the next INSERT takes a fresh sequence value, so
# the branch the demo/QA queries reference (4) silently drifts to 5, 6, 7...
# Never stolen: if some other branch already holds this id, fall back to auto.
DEMO_BRANCH_ID = 4

DEMO_OWNER_USERNAME = "demo_owner"
DEMO_PHONE_USERNAME = "demo_phone"
DEMO_ACCESSORY_USERNAME = "demo_accessory"

DEMO_USERNAMES = (
    DEMO_OWNER_USERNAME,
    DEMO_PHONE_USERNAME,
    DEMO_ACCESSORY_USERNAME,
)


PHONES_DATA = [
    # (model, storage, cost_price, sell_price, sold)
    ("iPhone 15 Pro Max",      "256",  1200, 1450, False),
    ("iPhone 15",              "128",  900,  1100, False),
    ("iPhone 14",              "128",  750,  900,  True),
    ("iPhone 13",              "128",  600,  750,  True),
    ("Samsung Galaxy S24",     "256",  850,  1050, False),
    ("Samsung S23 Ultra",      "512",  900,  1100, False),
    ("Samsung A55",            "128",  350,  450,  True),
    ("Xiaomi 14 Pro",          "512",  700,  870,  False),
    ("Xiaomi Redmi Note 13",   "256",  220,  290,  False),
    ("Google Pixel 8 Pro",     "256",  800,  980,  False),
    ("Honor Magic 6",          "256",  650,  820,  False),
    ("OnePlus 12",             "512",  750,  920,  True),
]

ACCESSORIES_DATA = [
    # (name, quantity, unit_cost, unit_sell, sold_qty, category_hint)
    ("Apple 20W Adapter",        20, 12,  18,  5,  "Adapter"),
    ("USB-C Cable 1m",           50, 3,   6,   15, "USB kabel"),
    ("iPhone 15 Pro Case",       30, 8,   15,  8,  "G‘ilof"),
    ("Samsung Tempered Glass",   40, 2,   5,   12, "Himoya oynasi"),
    ("AirPods Pro 2",            10, 180, 230, 3,  "Naushnik"),
    ("Xiaomi Power Bank 20000",  15, 25,  40,  4,  "Powerbank"),
    ("Wireless Charger 15W",     12, 18,  30,  2,  "Zaryadlagich"),
    ("Bluetooth Earphones",      25, 15,  28,  6,  "Bluetooth quloqchin"),
]

DEBTS_DATA = [
    # (customer_name, phone_note, amount, direction, seller_kind, partially_paid)
    ("Akmal Rahimov",   "+998901234567", 500, "WE_GAVE", "PHONE",     200),
    ("Dilshod Karimov", "+998901234568", 300, "WE_GAVE", "PHONE",     0),
    ("Nodira Salimova", "+998901234569", 150, "WE_GAVE", "ACCESSORY", 50),
    ("Sherzod Aliyev",  "+998901234570", 800, "WE_TOOK", "PHONE",     0),
]

EXPENSES_DATA = [
    # (description, amount, type, seller_kind)
    ("Do'kon ijarasi",         400, "SHOP_EXPENSE",     "PHONE"),
    ("Internet va kommunal",   80,  "SHOP_EXPENSE",     "PHONE"),
    ("Marketing reklama",      150, "SHOP_EXPENSE",     "ACCESSORY"),
    ("Tashish xizmati",        60,  "SHOP_EXPENSE",     "ACCESSORY"),
    ("Xodim bonusi",           200, "EMPLOYEE_EXPENSE", "PHONE"),
]

SALARIES_DATA = [
    # (employee_key, amount)
    ("PHONE",     500),
    ("ACCESSORY", 450),
]

EXTRA_PROFIT_DATA = [
    ("Qo'shimcha xizmat — sozlash", 30),
    ("Aksessuar bonus sotuv",       25),
]


# ==========================================================================
# MULTI-MONTH (`--months N`) CATALOGUES
#
# The single-month constants above are left untouched so `--months 1` keeps
# producing byte-identical data. The catalogues below are wider pools that the
# multi-month generator rotates through, so no two months look like copies.
# ==========================================================================

DEMO_SEED = 20260810  # fixed: repeated runs must produce the same demo

PHONE_CATALOG = [
    # (model, storage, cost_price, sell_price)
    ("iPhone 15 Pro Max",      "256",  1200, 1450),
    ("iPhone 15",              "128",  900,  1100),
    ("iPhone 14 Pro",          "256",  950,  1180),
    ("iPhone 14",              "128",  750,  900),
    ("iPhone 13",              "128",  600,  750),
    ("iPhone 12",              "64",   470,  590),
    ("Samsung Galaxy S24",     "256",  850,  1050),
    ("Samsung Galaxy S23",     "256",  700,  880),
    ("Samsung S23 Ultra",      "512",  900,  1100),
    ("Samsung Galaxy A55",     "128",  350,  450),
    ("Samsung Galaxy A35",     "128",  280,  370),
    ("Samsung Galaxy A15",     "128",  170,  235),
    ("Xiaomi 14 Pro",          "512",  700,  870),
    ("Xiaomi Redmi Note 13",   "256",  220,  290),
    ("Xiaomi Redmi Note 12",   "128",  180,  245),
    ("Xiaomi Poco X6",         "256",  260,  340),
    ("Google Pixel 8 Pro",     "256",  800,  980),
    ("Google Pixel 7a",        "128",  380,  490),
    ("Honor Magic 6",          "256",  650,  820),
    ("Honor X9b",              "256",  290,  380),
    ("OnePlus 12",             "512",  750,  920),
    ("OnePlus Nord 3",         "256",  400,  510),
    ("Infinix Note 40",        "256",  210,  285),
    ("Tecno Camon 30",         "256",  230,  305),
]

# Price tiers are interleaved on purpose: the per-month slice is a contiguous
# window of this list, so every month must get a mix of cheap high-turnover
# stock and a few high-ticket items — otherwise a month's accessory revenue
# cannot cover that month's accessory expenses, debts and salary.
ACCESSORY_CATALOG = [
    # (name, stock, unit_cost, unit_sell, category_hint)
    ("Zaryadnik Type-C 25W",     40, 9,   15,  "Adapter"),
    ("Quloqchin AirPods Pro 2",  10, 180, 230, "Naushnik"),
    ("USB-C kabel 1m",           50, 3,   6,   "USB kabel"),
    ("Xiaomi Power Bank 20000",  15, 25,  40,  "Powerbank"),
    ("Himoya oynasi 9D",         60, 2,   5,   "Himoya oynasi"),
    ("iPhone 15 Pro g'ilofi",    30, 8,   15,  "G‘ilof"),
    ("Bluetooth quloqchin",      25, 15,  28,  "Bluetooth quloqchin"),
    ("Apple 20W Adapter",        20, 12,  18,  "Adapter"),
    ("Quloqchin AirPods 3",      12, 130, 170, "Naushnik"),
    ("Lightning kabel 1m",       45, 3,   7,   "USB kabel"),
    ("Anker Power Bank 10000",   18, 18,  30,  "Powerbank"),
    ("Samsung himoya oynasi",    40, 2,   5,   "Himoya oynasi"),
    ("Samsung A55 g'ilofi",      35, 5,   11,  "G‘ilof"),
    ("Simsiz zaryadlagich 15W",  12, 18,  30,  "Zaryadlagich"),
    ("Avtomobil ushlagichi",     28, 6,   13,  "Adapter"),
    ("Smart Watch tasmasi",      22, 7,   14,  "Adapter"),
]

# A shop moves cables and glass by the handful and premium earphones one at a
# time; the quantity per sale follows the price tier.
PREMIUM_ACCESSORY_PRICE = Decimal("100")

DEBT_CUSTOMERS = [
    # (customer_name, phone_note, amount, direction, seller_kind, partially_paid)
    ("Aziz Karimov",     "+998901234567", 500, "WE_GAVE", "PHONE",     200),
    ("Dilshod Rahimov",  "+998901234568", 300, "WE_GAVE", "PHONE",     0),
    ("Nodira Yusupova",  "+998901234569", 150, "WE_GAVE", "ACCESSORY", 50),
    ("Sherzod Aliyev",   "+998901234570", 800, "WE_TOOK", "PHONE",     0),
    ("Kamola Tursunova", "+998901234571", 240, "WE_GAVE", "ACCESSORY", 120),
    ("Bobur Ergashev",   "+998901234572", 650, "WE_GAVE", "PHONE",     300),
    ("Malika Sodiqova",  "+998901234573", 190, "WE_GAVE", "ACCESSORY", 0),
    ("Rustam Nazarov",   "+998901234574", 450, "WE_TOOK", "PHONE",     150),
    ("Shahnoza Umarova", "+998901234575", 320, "WE_GAVE", "PHONE",     160),
    ("Otabek Jo'rayev",  "+998901234576", 210, "WE_GAVE", "ACCESSORY", 60),
]

EXPENSE_CATALOG = [
    # (description, amount, type, seller_kind)
    ("Do'kon ijarasi",         400, "SHOP_EXPENSE",     "PHONE"),
    ("Internet va kommunal",   80,  "SHOP_EXPENSE",     "PHONE"),
    ("Marketing reklama",      150, "SHOP_EXPENSE",     "ACCESSORY"),
    ("Tashish xizmati",        60,  "SHOP_EXPENSE",     "ACCESSORY"),
    ("Xodim bonusi",           200, "EMPLOYEE_EXPENSE", "PHONE"),
    ("Do'kon jihozlari",       120, "SHOP_EXPENSE",     "PHONE"),
    ("Qadoqlash materiallari", 45,  "SHOP_EXPENSE",     "ACCESSORY"),
    ("Xavfsizlik xizmati",     90,  "SHOP_EXPENSE",     "PHONE"),
]

EXTRA_PROFIT_CATALOG = [
    ("Qo'shimcha xizmat — sozlash",  30),
    ("Aksessuar bonus sotuv",        25),
    ("Ekran almashtirish xizmati",   40),
    ("Dastur o'rnatish xizmati",     18),
    ("Kafolat kengaytirish",         35),
    ("Ma'lumot ko'chirish xizmati",  22),
]

# Keyed by "months back from the current month": 0 = current (partial) month.
# The current month is deliberately smaller — only part of it has happened.
MONTH_VOLUMES = {
    0: {"phones": 8,  "phones_sold": 5,  "accessories": 7,  "accessory_sales": 9,  "debts": 3, "expenses": 3},
    1: {"phones": 18, "phones_sold": 13, "accessories": 14, "accessory_sales": 18, "debts": 6, "expenses": 6},
    2: {"phones": 15, "phones_sold": 11, "accessories": 12, "accessory_sales": 14, "debts": 5, "expenses": 6},
    3: {"phones": 12, "phones_sold": 8,  "accessories": 9,  "accessory_sales": 9,  "debts": 4, "expenses": 5},
}
OLDEST_MONTH_VOLUMES = MONTH_VOLUMES[3]

# Owner's phone-capital investment at the start of each month (growth story).
MONTH_INVESTMENTS = {0: 25000, 1: 22000, 2: 18000, 3: 15000}
OLDEST_MONTH_INVESTMENT = 15000


def _money(value):
    return Decimal(str(value))


def _shift_month(month_start, delta):
    """Return the first day of the month `delta` months away from `month_start`."""
    index = month_start.year * 12 + (month_start.month - 1) + delta
    year, month_zero = divmod(index, 12)
    return date(year, month_zero + 1, 1)


def _month_end(month_start):
    return _shift_month(month_start, 1) - timedelta(days=1)


def _drift(base, month_index):
    """Nudge a price by +4% per month so each month's rows stay distinct.

    AccessoryCreateService merges into an existing row when
    (branch, name, unit_cost) already exists and the month is not closed, so
    identical prices across months would collapse everything into one row dated
    in the oldest month. A small monthly price drift is both realistic and
    enough to keep one accessory row per month.
    """
    factor = Decimal("1") + (Decimal("4") * month_index / Decimal("100"))
    return (_money(base) * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@contextmanager
def _frozen_clock(moment):
    """Make `timezone.now()` return `moment` for the duration of the block.

    Every create-service resolves its capital month from `timezone.now()` /
    `timezone.localtime()`, and `added_at` is `auto_now_add`. Freezing the clock
    is what lets a back-dated record land in the right month's capital row while
    all business logic still runs through the service layer untouched.

    `timezone.localtime()` and `localdate()` call the module-level `now()`, so
    patching this single attribute covers them too. Nothing in `src/` imports
    `now` directly (`from django.utils.timezone import now`), so there is no
    stale reference to miss.
    """
    original_now = timezone.now
    timezone.now = lambda: moment
    try:
        yield
    finally:
        timezone.now = original_now


def _phone_category_hint(model_name):
    name_lower = model_name.lower()
    if "iphone" in name_lower:
        return "iPhone"
    if "samsung" in name_lower:
        return "Samsung"
    if "xiaomi" in name_lower or "redmi" in name_lower:
        return "Xiaomi"
    if "honor" in name_lower:
        return "Honor"
    if "pixel" in name_lower or "google" in name_lower:
        return "Huawei"
    if "oneplus" in name_lower:
        return "Oppo"
    return "iPhone"


class Command(BaseCommand):
    help = (
        "Generate idempotent demo data for Google Play / App Store review. "
        "Creates a single 'Demo Market' branch with 3 demo users, phones, "
        "accessories, debts, expenses, salaries, and extra profits. "
        "Use --force to wipe and regenerate."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Wipe existing demo branch and recreate it from scratch.",
        )
        parser.add_argument(
            "--months",
            type=int,
            default=1,
            help=(
                "How many months of history to generate, ending with the current "
                "month (default 1 = original single-month behaviour). The current "
                "month is filled only up to today."
            ),
        )

    # ---------- styling helpers ----------

    def _ok(self, message):
        self.stdout.write(self.style.SUCCESS(message))

    def _warn(self, message):
        self.stdout.write(self.style.WARNING(message))

    def _info(self, message):
        self.stdout.write(message)

    def _bold(self, message):
        self.stdout.write(self.style.SUCCESS(self.style.MIGRATE_HEADING(message)))

    # ---------- entrypoint ----------

    def handle(self, *args, **options):
        force = options.get("force", False)
        months = options.get("months") or 1
        if months < 1:
            self._warn("\n❌ --months qiymati kamida 1 bo'lishi kerak.\n")
            return

        exists = Branch.all_objects.filter(name=DEMO_BRANCH_NAME).exists()

        if exists and not force:
            self._warn(
                "\n⚠️  Demo Market allaqachon mavjud."
                "\n   Qaytadan yaratish uchun: python manage.py generate_demo --force\n"
            )
            return

        if months > 1:
            self._handle_multi_month(exists=exists, force=force, months=months)
            return

        try:
            with transaction.atomic():
                if exists and force:
                    self._info("🧹 Eski Demo Market tozalanmoqda...")
                    self._wipe_demo()

                self._step("1/10", "Userlar yaratilmoqda")
                owner, phone_seller, acc_seller = self._create_users()

                self._step("2/10", "Filial yaratilmoqda")
                branch = self._create_branch(owner)

                self._step("3/10", "Rollar biriktirilmoqda")
                self._assign_roles(branch, owner, phone_seller, acc_seller)

                self._step("4/10", "Telefon kategoriya tekshiruvi")
                self._ensure_phone_categories()

                self._step("5/10", "Aksessuar kategoriya tekshiruvi")
                self._ensure_accessory_categories()

                self._step("6/10", "Owner $15,000 invest qilmoqda")
                phone_capital = PhoneCapitalService.add_investment(
                    owner=owner, branch=branch, amount=_money(15000),
                )

                self._step("7/10", "Telefonlar va sotuvlar yaratilmoqda")
                phone_stats = self._create_phones(branch, phone_seller)

                self._step("8/10", "Aksessuarlar va sotuvlar yaratilmoqda")
                accessory_stats = self._create_accessories(branch, acc_seller)

                self._step("9/10", "Qarz, xarajat, oylik, qo'shimcha foyda")
                debt_count = self._create_debts(branch, phone_seller, acc_seller, owner)
                expense_count = self._create_expenses(branch, phone_seller, acc_seller)
                salary_count = self._create_salaries(branch, owner, phone_seller, acc_seller)
                extra_count = self._create_extra_profits(branch, phone_seller)

                self._step("10/10", "Yakuniy ma'lumotlar yig'ilmoqda")
                phone_capital.refresh_from_db()
                accessory_capital = AccessoryCapital.objects.filter(branch=branch).first()

            self._print_summary(
                phone_capital=phone_capital,
                accessory_capital=accessory_capital,
                phone_stats=phone_stats,
                accessory_stats=accessory_stats,
                debt_count=debt_count,
                expense_count=expense_count,
                salary_count=salary_count,
                extra_count=extra_count,
            )
        except Exception as exc:
            self._warn(f"\n❌ XATO: {type(exc).__name__}: {exc}")
            self._warn("Hech qanday o'zgarish saqlanmadi (transaction rollback).\n")
            raise

    # ---------- step printer ----------

    def _step(self, prefix, label):
        self._ok(f"   [{prefix}] {label}...")

    # ======================================================================
    # MULTI-MONTH FLOW (`--months N`, N > 1)
    #
    # Kept as a separate entrypoint so `--months 1` runs the original code
    # path byte-for-byte — no regression for the existing demo setup.
    # ======================================================================

    def _handle_multi_month(self, *, exists, force, months):
        self._rng = random.Random(DEMO_SEED)
        # Captured before any clock freezing: the hard "nothing in the future" ceiling.
        self._max_dt = timezone.now()
        self._imei_counter = 0

        windows = self._month_windows(months)

        try:
            with transaction.atomic():
                if exists and force:
                    self._info("🧹 Eski Demo Market tozalanmoqda...")
                    self._wipe_demo()

                self._step("1/6", "Userlar yaratilmoqda")
                owner, phone_seller, acc_seller = self._create_users()

                self._step("2/6", "Filial yaratilmoqda")
                branch = self._create_branch(owner)

                self._step("3/6", "Rollar biriktirilmoqda")
                self._assign_roles(branch, owner, phone_seller, acc_seller)

                self._step("4/6", "Kategoriya tekshiruvi")
                self._ensure_phone_categories()
                self._ensure_accessory_categories()

                self._step("5/6", f"{months} oylik tarix yaratilmoqda")
                month_reports = []
                for position, window in enumerate(windows):
                    month_reports.append(
                        self._generate_month(
                            branch=branch,
                            owner=owner,
                            phone_seller=phone_seller,
                            accessory_seller=acc_seller,
                            window=window,
                            month_index=position,
                        )
                    )

                self._step("6/6", "Yakuniy ma'lumotlar yig'ilmoqda")
                for report in month_reports:
                    self._attach_capital_figures(branch, report)

            self._print_multi_month_summary(month_reports)
        except Exception as exc:
            self._warn(f"\n❌ XATO: {type(exc).__name__}: {exc}")
            self._warn("Hech qanday o'zgarish saqlanmadi (transaction rollback).\n")
            raise

    # ---------- month planning ----------

    def _month_windows(self, months):
        """Oldest-first list of (month_start, month_end, months_back).

        `month_end` is the real last day of the month, except for the current
        month where it is today — nothing may be dated in the future.
        """
        today = timezone.localdate()
        current_month_start = today.replace(day=1)

        windows = []
        for back in range(months - 1, -1, -1):
            month_start = _shift_month(current_month_start, -back)
            month_end = today if back == 0 else _month_end(month_start)
            windows.append((month_start, month_end, back))
        return windows

    def _volumes_for(self, months_back):
        return MONTH_VOLUMES.get(months_back, OLDEST_MONTH_VOLUMES)

    def _investment_for(self, months_back):
        return MONTH_INVESTMENTS.get(months_back, OLDEST_MONTH_INVESTMENT)

    # ---------- date helpers ----------

    def _clamp(self, moment):
        """Never let a generated timestamp reach into the future."""
        ceiling = self._max_dt - timedelta(minutes=1)
        return moment if moment <= ceiling else ceiling

    def _at(self, day, *, hour_from=9, hour_to=18):
        """Aware datetime on `day` at a seeded random working-hours moment."""
        moment = timezone.make_aware(
            datetime.combine(
                day,
                time(
                    self._rng.randint(hour_from, hour_to),
                    self._rng.randint(0, 59),
                    self._rng.randint(0, 59),
                ),
            ),
            timezone.get_current_timezone(),
        )
        return self._clamp(moment)

    def _spread_days(self, month_start, month_end, count, *, tail_margin=0):
        """`count` seeded days inside the window, sorted, leaving a tail margin.

        `tail_margin` reserves the last N days so a follow-up event (a sale a
        few days after the phone was added) still fits inside the same month.
        """
        span = (month_end - month_start).days
        last_offset = max(0, span - tail_margin)
        return sorted(
            month_start + timedelta(days=self._rng.randint(0, last_offset))
            for _ in range(count)
        )

    def _rotate(self, catalog, months_back, count, step):
        """Take `count` distinct entries from `catalog`, rotated per month."""
        offset = (months_back * step) % len(catalog)
        return [catalog[(offset + i) % len(catalog)] for i in range(count)]

    # ---------- one month ----------

    def _generate_month(self, *, branch, owner, phone_seller, accessory_seller, window, month_index):
        month_start, month_end, months_back = window
        volumes = self._volumes_for(months_back)

        report = {
            "month_start": month_start,
            "month_end": month_end,
            "partial": months_back == 0,
        }

        # Owner invests at the start of the month, before any purchase.
        investment = self._investment_for(months_back)
        with _frozen_clock(self._at(month_start, hour_from=9, hour_to=10)):
            PhoneCapitalService.add_investment(
                owner=owner, branch=branch, amount=_money(investment),
            )
            # Guarantee an AccessoryCapital row for this month even before the
            # first accessory purchase touches it.
            CapitalService.get_accessory_capital(branch, month_start)
        report["investment"] = _money(investment)

        report.update(
            self._create_phones_for_month(
                branch, phone_seller, window=window, volumes=volumes,
            )
        )
        report.update(
            self._create_accessories_for_month(
                branch,
                accessory_seller,
                window=window,
                volumes=volumes,
                month_index=month_index,
            )
        )
        report["debts"] = self._create_debts_for_month(
            branch, phone_seller, accessory_seller, owner,
            window=window, volumes=volumes,
        )
        report["expenses"] = self._create_expenses_for_month(
            branch, phone_seller, accessory_seller, window=window, volumes=volumes,
        )
        report["salaries"] = self._create_salaries_for_month(
            branch, owner, phone_seller, accessory_seller,
            window=window, month_index=month_index,
        )
        report["extra_profits"] = self._create_extra_profits_for_month(
            branch, phone_seller, window=window,
        )
        return report

    # ---------- phones (dated) ----------

    def _create_phones_for_month(self, branch, phone_seller, *, window, volumes):
        month_start, month_end, months_back = window
        wanted = volumes["phones"]
        models = self._rotate(PHONE_CATALOG, months_back, wanted, step=5)
        # Reserve the month tail so every sale still lands inside its own month.
        added_days = self._spread_days(month_start, month_end, wanted, tail_margin=2)

        created = []
        for (model_name, storage, cost, sell_price), added_day in zip(models, added_days):
            self._imei_counter += 1
            added_dt = self._at(added_day)

            with _frozen_clock(added_dt):
                phone = PhoneCreateService.create_phone(
                    validated_data={
                        "name": model_name,
                        "category": self._resolve_phone_category(model_name),
                        "branch": branch,
                        "imei": f"3500{self._imei_counter:011d}",
                        "storage": storage,
                        "color": "Black",
                        "from_by": "Demo supplier",
                        "cost_price": _money(cost),
                    },
                    added_by=phone_seller,
                )
            Phone.objects.filter(pk=phone.pk).update(added_at=added_dt)
            created.append((phone, added_day, added_dt, sell_price))

        sold = 0
        for phone, added_day, added_dt, sell_price in self._rng.sample(
            created, k=min(volumes["phones_sold"], len(created))
        ):
            # Sold some days after it was added, never before, never same second.
            sold_day = min(added_day + timedelta(days=self._rng.randint(2, 7)), month_end)
            sold_dt = self._at(sold_day, hour_from=10, hour_to=19)
            if sold_dt <= added_dt:
                # Only reachable if the clamp pulled the sale back to "now";
                # leave the phone in stock rather than invent an impossible sale.
                continue

            with _frozen_clock(sold_dt):
                PhoneSellService.sell_phone(
                    phone=phone,
                    sell_price=_money(sell_price),
                    sold_by=phone_seller,
                )
            Phone.objects.filter(pk=phone.pk).update(added_at=added_dt, sold_at=sold_dt)
            sold += 1

        return {"phones": len(created), "phones_sold": sold}

    # ---------- accessories (dated) ----------

    def _create_accessories_for_month(
        self, branch, accessory_seller, *, window, volumes, month_index
    ):
        month_start, month_end, months_back = window
        wanted = volumes["accessories"]
        items = self._rotate(ACCESSORY_CATALOG, months_back, wanted, step=5)
        added_days = self._spread_days(month_start, month_end, wanted, tail_margin=2)

        created = []
        for (name, stock, cost, sell, category_hint), added_day in zip(items, added_days):
            added_dt = self._at(added_day)
            unit_cost = _drift(cost, month_index)
            unit_sell = _drift(sell, month_index)

            with _frozen_clock(added_dt):
                accessory = AccessoryCreateService.create_accessory(
                    validated_data={
                        "name": name,
                        "category": self._resolve_accessory_category(category_hint),
                        "branch": branch,
                        "unit_cost": unit_cost,
                        "stock": stock,
                    },
                    added_by=accessory_seller,
                )
            Accessory.objects.filter(pk=accessory.pk).update(added_at=added_dt)
            created.append({"accessory": accessory, "added_day": added_day, "sell": unit_sell})

        sold_units = 0
        sale_count = 0
        for _ in range(volumes["accessory_sales"]):
            entry = self._rng.choice(created)
            accessory = entry["accessory"]
            accessory.refresh_from_db(fields=["stock"])
            if accessory.stock < 1:
                continue

            if entry["sell"] >= PREMIUM_ACCESSORY_PRICE:
                quantity = min(accessory.stock, self._rng.randint(1, 2))
            else:
                quantity = min(accessory.stock, self._rng.randint(4, 11))
            sold_day = min(
                entry["added_day"] + timedelta(days=self._rng.randint(1, 12)), month_end
            )
            sold_dt = self._at(sold_day, hour_from=10, hour_to=19)

            with _frozen_clock(sold_dt):
                sale = AccessorySellService.sell_accessory(
                    accessory=accessory,
                    quantity=quantity,
                    total_price=entry["sell"] * quantity,
                    sold_by=accessory_seller,
                )
            AccessorySale.objects.filter(pk=sale.pk).update(added_at=sold_dt, sold_at=sold_dt)
            sold_units += quantity
            sale_count += 1

        return {
            "accessories": len(created),
            "accessory_sales": sale_count,
            "accessory_units": sold_units,
        }

    # ---------- debts (dated) ----------

    def _create_debts_for_month(
        self, branch, phone_seller, accessory_seller, owner, *, window, volumes
    ):
        month_start, month_end, months_back = window
        wanted = volumes["debts"]
        rows = self._rotate(DEBT_CUSTOMERS, months_back, wanted, step=3)
        days = self._spread_days(month_start, month_end, wanted, tail_margin=3)

        count = 0
        for (f_name, phone_note, amount, direction, seller_kind, partially_paid), day in zip(rows, days):
            creator = phone_seller if seller_kind == "PHONE" else accessory_seller
            created_dt = self._at(day)

            with _frozen_clock(created_dt):
                debt = DebtCreateService.create_debt(
                    branch=branch,
                    f_name=f_name,
                    amount=_money(amount),
                    direction=direction,
                    created_by=creator,
                    note=f"Tel: {phone_note}",
                )
            Debt.objects.filter(pk=debt.pk).update(added_at=created_dt)
            count += 1

            if partially_paid > 0:
                paid_day = min(day + timedelta(days=self._rng.randint(2, 10)), month_end)
                paid_dt = self._at(paid_day, hour_from=10, hour_to=19)
                if paid_dt <= created_dt:
                    continue
                # DebtPaymentService only allows payments in the debt's own month,
                # which the frozen clock satisfies. Owner has access to all domains.
                with _frozen_clock(paid_dt):
                    payment = DebtPaymentService.pay_debt(
                        debt=debt,
                        amount=_money(partially_paid),
                        paid_by=owner,
                        note="Qisman to'lov (demo)",
                    )
                DebtPayment.objects.filter(pk=payment.pk).update(added_at=paid_dt)
        return count

    # ---------- expenses (dated) ----------

    def _create_expenses_for_month(
        self, branch, phone_seller, accessory_seller, *, window, volumes
    ):
        month_start, month_end, months_back = window
        wanted = volumes["expenses"]
        rows = self._rotate(EXPENSE_CATALOG, months_back, wanted, step=2)
        days = self._spread_days(month_start, month_end, wanted)

        count = 0
        for (description, amount, expense_type, seller_kind), day in zip(rows, days):
            creator = phone_seller if seller_kind == "PHONE" else accessory_seller
            created_dt = self._at(day)

            with _frozen_clock(created_dt):
                expense = ExpenseCreateService.create_expense(
                    validated_data={
                        "branch": branch,
                        "type": expense_type,
                        "amount": _money(amount),
                        "note": description,
                    },
                    created_by=creator,
                )
            Expense.objects.filter(pk=expense.pk).update(added_at=created_dt)
            count += 1
        return count

    # ---------- salaries (dated) ----------

    def _create_salaries_for_month(
        self, branch, owner, phone_seller, accessory_seller, *, window, month_index
    ):
        month_start, month_end, _months_back = window
        # Near month end; in a partial month it reads as an advance payment.
        pay_day = max(month_start, month_end - timedelta(days=2))

        count = 0
        for employee_kind, amount in SALARIES_DATA:
            employee = phone_seller if employee_kind == "PHONE" else accessory_seller
            created_dt = self._at(pay_day)

            with _frozen_clock(created_dt):
                salary = SalaryCreateService.create_salary(
                    validated_data={
                        "branch": branch,
                        "employee": employee,
                        "amount": _money(amount + 25 * month_index),
                        "note": f"{employee.first_name} uchun oylik (demo)",
                    },
                    created_by=owner,
                )
            Salary.objects.filter(pk=salary.pk).update(added_at=created_dt)
            count += 1
        return count

    # ---------- extra profit (dated) ----------

    def _create_extra_profits_for_month(self, branch, phone_seller, *, window):
        month_start, month_end, months_back = window
        rows = self._rotate(EXTRA_PROFIT_CATALOG, months_back, 2, step=2)
        days = self._spread_days(month_start, month_end, 2)

        count = 0
        for (note, amount), day in zip(rows, days):
            created_dt = self._at(day)
            with _frozen_clock(created_dt):
                extra_profit = ExtraProfitCreateService.create_extra_profit(
                    validated_data={
                        "branch": branch,
                        "amount": _money(amount),
                        "note": note,
                    },
                    created_by=phone_seller,
                )
            ExtraProfit.objects.filter(pk=extra_profit.pk).update(added_at=created_dt)
            count += 1
        return count

    # ---------- multi-month summary ----------

    def _attach_capital_figures(self, branch, report):
        month_start = report["month_start"]
        phone_capital = PhoneCapital.objects.filter(branch=branch, month=month_start).first()
        accessory_capital = AccessoryCapital.objects.filter(
            branch=branch, month=month_start
        ).first()
        report["phone_capital"] = phone_capital
        report["accessory_capital"] = accessory_capital

    def _print_multi_month_summary(self, month_reports):
        sep = "=" * 78
        self._info("")
        self._ok(sep)
        self._ok(f"✅ DEMO DATA YARATILDI — {len(month_reports)} OYLIK TARIX")
        self._ok(sep)
        self._info("")
        self._info(f"📦 Branch:        {DEMO_BRANCH_NAME}")
        self._info(f"👥 Userlar (parol: {DEMO_PASSWORD}, PIN: {DEMO_PIN}):")
        self._info(f"   • {DEMO_OWNER_USERNAME:<14} (Sardor Karimov)   — Owner")
        self._info(f"   • {DEMO_PHONE_USERNAME:<14} (Jasur Toshmatov)  — Phone Seller")
        self._info(f"   • {DEMO_ACCESSORY_USERNAME:<14} (Bekzod Yusupov)   — Accessory Seller")
        self._info("")

        header = (
            f"{'Oy':<10}{'Tel':>5}{'Sot':>5}{'Aks':>5}{'AksSot':>8}"
            f"{'Qarz':>6}{'Xarj':>6}{'Oylik':>7}{'Extra':>7}"
            f"{'Tel.balans':>13}{'Aks.balans':>13}"
        )
        self._info(header)
        self._info("-" * len(header))

        for report in month_reports:
            phone_capital = report["phone_capital"]
            accessory_capital = report["accessory_capital"]
            phone_balance = phone_capital.current_balance if phone_capital else Decimal("0")
            acc_balance = accessory_capital.current_balance if accessory_capital else Decimal("0")
            label = report["month_start"].strftime("%Y-%m")
            if report["partial"]:
                label += "*"
            self._info(
                f"{label:<10}{report['phones']:>5}{report['phones_sold']:>5}"
                f"{report['accessories']:>5}{report['accessory_sales']:>8}"
                f"{report['debts']:>6}{report['expenses']:>6}"
                f"{report['salaries']:>7}{report['extra_profits']:>7}"
                f"{phone_balance:>13,.2f}{acc_balance:>13,.2f}"
            )

        last = month_reports[-1]
        self._info("")
        self._info(
            f"* {last['month_start']:%Y-%m} joriy oy — faqat "
            f"{last['month_end']:%d-%B} kunigacha to'ldirildi (kelajakdagi sana yo'q)."
        )
        self._info("💰 Har oy uchun alohida PhoneCapital va AccessoryCapital qatori yaratildi.")
        self._info("🚫 close_month CHAQIRILMADI — rollover bug'i demoni buzardi (docstring'ga qarang).")
        self._info("")
        self._ok(sep)
        self._info("Endi mobile'da test qiling:")
        self._info(
            f"  Username: {DEMO_OWNER_USERNAME} / "
            f"{DEMO_PHONE_USERNAME} / {DEMO_ACCESSORY_USERNAME}"
        )
        self._info(f"  Password: {DEMO_PASSWORD}")
        self._info(f"  PIN:      {DEMO_PIN}")
        self._ok(sep)
        self._info("")

    # ---------- wipe ----------

    def _wipe_demo(self):
        branch = Branch.all_objects.filter(name=DEMO_BRANCH_NAME).first()
        if branch is None:
            return

        # Order matters: dependants first.
        Journal.all_objects.filter(branch=branch).delete()
        # Leftovers from an earlier close_month run on the demo branch: without
        # this the demo still looks "closed" in May and the dashboard reads a
        # stale snapshot instead of the freshly generated months.
        DashboardSnapshot.objects.filter(branch=branch).delete()
        MonthClosingRecord.all_objects.filter(branch=branch).delete()
        DebtMonthlySnapshot.objects.filter(branch=branch).delete()
        DebtPayment.all_objects.filter(debt__branch=branch).delete()
        Debt.all_objects.filter(branch=branch).delete()
        AccessorySale.all_objects.filter(branch=branch).delete()
        Accessory.all_objects.filter(branch=branch).delete()
        Phone.all_objects.filter(branch=branch).delete()
        ExtraProfit.all_objects.filter(branch=branch).delete()
        Salary.all_objects.filter(branch=branch).delete()
        Expense.all_objects.filter(branch=branch).delete()
        PhoneCapital.all_objects.filter(branch=branch).delete()
        AccessoryCapital.all_objects.filter(branch=branch).delete()
        BranchUser.all_objects.filter(branch=branch).delete()

        branch_pk = branch.pk
        # Branch.owner is PROTECT; delete demo users AFTER branch is gone.
        Branch.all_objects.filter(pk=branch_pk).delete()
        # Journal entries by demo users may still exist (e.g. DebtPayment
        # journals have no branch FK and were missed by the branch-scoped purge).
        Journal.all_objects.filter(user__username__in=DEMO_USERNAMES).delete()
        User.all_objects.filter(username__in=DEMO_USERNAMES).delete()

    # ---------- users ----------

    def _create_users(self):
        owner = self._create_user(
            username=DEMO_OWNER_USERNAME,
            first_name="Sardor",
            last_name="Karimov",
            phone="+998901112233",
        )
        phone_seller = self._create_user(
            username=DEMO_PHONE_USERNAME,
            first_name="Jasur",
            last_name="Toshmatov",
            phone="+998902223344",
        )
        accessory_seller = self._create_user(
            username=DEMO_ACCESSORY_USERNAME,
            first_name="Bekzod",
            last_name="Yusupov",
            phone="+998903334455",
        )
        return owner, phone_seller, accessory_seller

    def _create_user(self, *, username, first_name, last_name, phone):
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_active=True,
            is_vip=True,
            account_status="vip",
        )
        user.set_password(DEMO_PASSWORD)
        user.set_mobile_pin(DEMO_PIN)
        user.save()
        return user

    # ---------- branch ----------

    def _create_branch(self, owner):
        data = {
            "name": DEMO_BRANCH_NAME,
            "owner": owner,
            "address": "Demo demo ko'chasi, 1-uy",
            "is_active": True,
        }
        if not Branch.all_objects.filter(pk=DEMO_BRANCH_ID).exists():
            data["id"] = DEMO_BRANCH_ID
        return Branch.objects.create(**data)

    def _assign_roles(self, branch, owner, phone_seller, accessory_seller):
        BranchUser.objects.create(user=owner, branch=branch, role=BranchUser.ROLE_OWNER)
        BranchUser.objects.create(
            user=phone_seller, branch=branch, role=BranchUser.ROLE_PHONE_SELLER,
        )
        BranchUser.objects.create(
            user=accessory_seller, branch=branch, role=BranchUser.ROLE_ACCESSORY_SELLER,
        )
        # Bust cached_property on role_map so service permission checks see the new roles.
        for user in (owner, phone_seller, accessory_seller):
            for attr in ("roles", "_role_branch_map"):
                if attr in user.__dict__:
                    del user.__dict__[attr]

    # ---------- categories ----------

    def _ensure_phone_categories(self):
        if not PhoneCategory.objects.exists():
            raise RuntimeError(
                "Bazada birorta ham telefon kategoriyasi yo'q. "
                "Avval `python manage.py load_initial_data` ishlating yoki "
                "qo'lda bitta PhoneCategory yarating."
            )

    def _ensure_accessory_categories(self):
        if not AccessoryCategory.objects.exists():
            raise RuntimeError(
                "Bazada birorta ham aksessuar kategoriyasi yo'q. "
                "Avval `python manage.py load_initial_data` ishlating yoki "
                "qo'lda bitta AccessoryCategory yarating."
            )

    def _resolve_phone_category(self, model_name):
        """Find best-matching PhoneCategory; fall back to any available."""
        hint = _phone_category_hint(model_name)
        category = PhoneCategory.objects.filter(name=hint).first()
        if category:
            return category
        # iPhone exists per user guarantee; try it as a generic fallback.
        category = PhoneCategory.objects.filter(name="iPhone").first()
        if category:
            return category
        return PhoneCategory.objects.first()

    def _resolve_accessory_category(self, hint):
        """Find best-matching AccessoryCategory; fall back to any available."""
        category = AccessoryCategory.objects.filter(name=hint).first()
        if category:
            return category
        return AccessoryCategory.objects.first()

    # ---------- phones ----------

    def _create_phones(self, branch, phone_seller):
        added, sold = 0, 0
        for index, (model_name, storage, cost, sell_price, is_sold) in enumerate(PHONES_DATA, start=1):
            category = self._resolve_phone_category(model_name)

            phone = PhoneCreateService.create_phone(
                validated_data={
                    "name": model_name,
                    "category": category,
                    "branch": branch,
                    "imei": f"3500{index:02d}000000000",
                    "storage": storage,
                    "color": "Black",
                    "from_by": "Demo supplier",
                    "cost_price": _money(cost),
                },
                added_by=phone_seller,
            )
            added += 1

            if is_sold:
                PhoneSellService.sell_phone(
                    phone=phone,
                    sell_price=_money(sell_price),
                    sold_by=phone_seller,
                )
                sold += 1

        return {"total": added, "sold": sold, "stock": added - sold}

    # ---------- accessories ----------

    def _create_accessories(self, branch, accessory_seller):
        total_products = 0
        sold_units = 0
        for name, quantity, cost, sell, sold_qty, category_hint in ACCESSORIES_DATA:
            category = self._resolve_accessory_category(category_hint)

            accessory = AccessoryCreateService.create_accessory(
                validated_data={
                    "name": name,
                    "category": category,
                    "branch": branch,
                    "unit_cost": _money(cost),
                    "stock": quantity,
                },
                added_by=accessory_seller,
            )
            total_products += 1

            if sold_qty > 0:
                AccessorySellService.sell_accessory(
                    accessory=accessory,
                    quantity=sold_qty,
                    total_price=_money(sell * sold_qty),
                    sold_by=accessory_seller,
                )
                sold_units += sold_qty

        return {"total": total_products, "sold_units": sold_units}

    # ---------- debts ----------

    def _create_debts(self, branch, phone_seller, accessory_seller, owner):
        count = 0
        for f_name, phone_note, amount, direction, seller_kind, partially_paid in DEBTS_DATA:
            creator = phone_seller if seller_kind == "PHONE" else accessory_seller
            debt = DebtCreateService.create_debt(
                branch=branch,
                f_name=f_name,
                amount=_money(amount),
                direction=direction,
                created_by=creator,
                note=f"Tel: {phone_note}",
            )
            count += 1

            if partially_paid > 0:
                # Owner has access to all domains via user_matches_debt_domain.
                DebtPaymentService.pay_debt(
                    debt=debt,
                    amount=_money(partially_paid),
                    paid_by=owner,
                    note="Qisman to'lov (demo)",
                )
        return count

    # ---------- expenses ----------

    def _create_expenses(self, branch, phone_seller, accessory_seller):
        count = 0
        for description, amount, expense_type, seller_kind in EXPENSES_DATA:
            creator = phone_seller if seller_kind == "PHONE" else accessory_seller
            ExpenseCreateService.create_expense(
                validated_data={
                    "branch": branch,
                    "type": expense_type,
                    "amount": _money(amount),
                    "note": description,
                },
                created_by=creator,
            )
            count += 1
        return count

    # ---------- salaries ----------

    def _create_salaries(self, branch, owner, phone_seller, accessory_seller):
        count = 0
        for employee_kind, amount in SALARIES_DATA:
            employee = phone_seller if employee_kind == "PHONE" else accessory_seller
            SalaryCreateService.create_salary(
                validated_data={
                    "branch": branch,
                    "employee": employee,
                    "amount": _money(amount),
                    "note": f"{employee.first_name} uchun oylik (demo)",
                },
                created_by=owner,
            )
            count += 1
        return count

    # ---------- extra profit ----------

    def _create_extra_profits(self, branch, phone_seller):
        count = 0
        for note, amount in EXTRA_PROFIT_DATA:
            ExtraProfitCreateService.create_extra_profit(
                validated_data={
                    "branch": branch,
                    "amount": _money(amount),
                    "note": note,
                },
                created_by=phone_seller,
            )
            count += 1
        return count

    # ---------- summary ----------

    def _print_summary(
        self,
        *,
        phone_capital,
        accessory_capital,
        phone_stats,
        accessory_stats,
        debt_count,
        expense_count,
        salary_count,
        extra_count,
    ):
        sep = "=" * 60
        self._info("")
        self._ok(sep)
        self._ok("✅ DEMO DATA MUVAFFAQIYATLI YARATILDI")
        self._ok(sep)
        self._info("")
        self._info(f"📦 Branch:        {DEMO_BRANCH_NAME}")
        self._info("")
        self._info(f"👥 Userlar (parol: {DEMO_PASSWORD}, PIN: {DEMO_PIN}):")
        self._info(f"   • {DEMO_OWNER_USERNAME:<14} (Sardor Karimov)   — Owner")
        self._info(f"   • {DEMO_PHONE_USERNAME:<14} (Jasur Toshmatov)  — Phone Seller")
        self._info(f"   • {DEMO_ACCESSORY_USERNAME:<14} (Bekzod Yusupov)   — Accessory Seller")
        self._info("")

        phone_invested = phone_capital.invested_amount if phone_capital else Decimal("0")
        phone_balance = phone_capital.current_balance if phone_capital else Decimal("0")
        acc_invested = accessory_capital.invested_amount if accessory_capital else Decimal("0")
        acc_balance = accessory_capital.current_balance if accessory_capital else Decimal("0")

        self._info("💰 Capital:")
        self._info(f"   • Phone:     ${phone_invested:,.2f} invest, ${phone_balance:,.2f} current")
        self._info(f"   • Accessory: ${acc_invested:,.2f} invested, ${acc_balance:,.2f} current")
        self._info("")
        self._info(
            f"📱 Telefonlar:    {phone_stats['total']} ta "
            f"({phone_stats['stock']} stock + {phone_stats['sold']} sotilgan)"
        )
        self._info(
            f"🎧 Aksessuarlar:  {accessory_stats['total']} ta product, "
            f"{accessory_stats['sold_units']} ta sotilgan"
        )
        self._info(f"💳 Qarzlar:       {debt_count} ta")
        self._info(f"💸 Xarajatlar:    {expense_count} ta")
        self._info(f"💵 Oyliklar:      {salary_count} ta")
        self._info(f"🎁 Extra profit:  {extra_count} ta")
        self._info("")
        self._ok(sep)
        self._info("Endi mobile'da test qiling:")
        self._info(
            f"  Username: {DEMO_OWNER_USERNAME} / "
            f"{DEMO_PHONE_USERNAME} / {DEMO_ACCESSORY_USERNAME}"
        )
        self._info(f"  Password: {DEMO_PASSWORD}")
        self._info(f"  PIN:      {DEMO_PIN}")
        self._ok(sep)
        self._info("")

"""Tests for dashboard comparison analytics (previous month + all-time average)."""
from datetime import datetime, date
from decimal import Decimal

import pytest
from django.utils import timezone

from src.core import models
from src.services.dashboard import DashboardService


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _aware(year, month, day=15):
    return timezone.make_aware(datetime(year, month, day, 10, 0, 0))


def _today():
    return timezone.localdate()


def _current_ym():
    today = _today()
    return today.year, today.month


def _prev_ym():
    today = _today()
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def _two_months_ago_ym():
    y, m = _prev_ym()
    if m == 1:
        return y - 1, 12
    return y, m - 1


# ---------------------------------------------------------------------------
# compare_metric unit tests
# ---------------------------------------------------------------------------

def test_compare_metric_up():
    result = DashboardService.compare_metric(Decimal("1000"), Decimal("800"), mode="previous")
    assert result["direction"] == "up"
    assert result["percent"] == 25.0
    assert result["current"] == "1000.00"
    assert result["previous"] == "800.00"
    assert result["diff"] == "200.00"


def test_compare_metric_down():
    result = DashboardService.compare_metric(Decimal("300"), Decimal("400"), mode="previous")
    assert result["direction"] == "down"
    assert result["percent"] == -25.0


def test_compare_metric_neutral():
    result = DashboardService.compare_metric(Decimal("500"), Decimal("500"), mode="previous")
    assert result["direction"] == "neutral"
    assert result["percent"] == 0.0


def test_compare_metric_zero_previous_positive_current():
    result = DashboardService.compare_metric(Decimal("500"), Decimal("0"), mode="previous")
    assert result["direction"] == "up"
    assert result["percent"] is None


def test_compare_metric_both_zero():
    result = DashboardService.compare_metric(0, 0, mode="previous")
    assert result["direction"] == "neutral"
    assert result["percent"] == 0


def test_compare_metric_alltime_mode():
    result = DashboardService.compare_metric(Decimal("900"), Decimal("600"), mode="alltime")
    assert "average" in result
    assert "previous" not in result
    assert result["average"] == "600.00"


def test_compare_metric_none_inputs_safe():
    result = DashboardService.compare_metric(None, None, mode="previous")
    assert result["direction"] == "neutral"
    assert result["current"] == "0.00"


# ---------------------------------------------------------------------------
# get_previous_month helper
# ---------------------------------------------------------------------------

def test_get_previous_month_mid_year():
    assert DashboardService.get_previous_month(2026, 4) == (2026, 3)


def test_get_previous_month_january_wraps():
    assert DashboardService.get_previous_month(2026, 1) == (2025, 12)


# ---------------------------------------------------------------------------
# Phone dashboard comparison: previous month
# ---------------------------------------------------------------------------

def test_phone_comparison_previous_month(branches, categories, users, set_model_datetime):
    branch = branches["main"]
    cy, cm = _current_ym()
    py, pm = _prev_ym()

    # Create a sold phone in previous month
    phone = models.Phone.objects.create(
        name="OldPhone",
        category=categories["phone"],
        branch=branch,
        imei="IMEI-PREV-001",
        storage="64",
        color="Black",
        from_by="Supplier",
        cost_price=Decimal("400.00"),
        added_by=users["owner"],
        is_sold=True,
        sell_price=Decimal("600.00"),
    )
    set_model_datetime(phone, added_at=_aware(py, pm), sold_at=_aware(py, pm))

    # Create a sold phone in current month (higher value)
    phone2 = models.Phone.objects.create(
        name="NewPhone",
        category=categories["phone"],
        branch=branch,
        imei="IMEI-CUR-001",
        storage="128",
        color="White",
        from_by="Supplier",
        cost_price=Decimal("500.00"),
        added_by=users["owner"],
        is_sold=True,
        sell_price=Decimal("800.00"),
    )
    set_model_datetime(phone2, added_at=_aware(cy, cm), sold_at=_aware(cy, cm))

    comparison = DashboardService.get_phone_dashboard_comparison(branch, cy, cm)

    pm_cmp = comparison["previous_month"]
    assert pm_cmp["total_sold_value"]["current"] == "800.00"
    assert pm_cmp["total_sold_value"]["previous"] == "600.00"
    assert pm_cmp["total_sold_value"]["direction"] == "up"
    assert pm_cmp["phones_sold_count"]["current"] == "1.00"
    assert pm_cmp["phones_sold_count"]["previous"] == "1.00"
    assert pm_cmp["phones_sold_count"]["direction"] == "neutral"


def test_phone_comparison_previous_month_no_data(branches):
    branch = branches["main"]
    cy, cm = _current_ym()

    comparison = DashboardService.get_phone_dashboard_comparison(branch, cy, cm)

    pm = comparison["previous_month"]
    assert pm["total_sold_value"]["direction"] == "neutral"
    assert pm["total_sold_value"]["current"] == "0.00"
    assert pm["total_sold_value"]["previous"] == "0.00"


# ---------------------------------------------------------------------------
# Phone dashboard comparison: all-time average
# ---------------------------------------------------------------------------

def test_phone_comparison_alltime(branches, categories, users, set_model_datetime):
    branch = branches["main"]
    cy, cm = _current_ym()
    py, pm = _prev_ym()
    ty, tm = _two_months_ago_ym()

    for imei, month_y, month_m, sell in [
        ("IMEI-T1", ty, tm, Decimal("900.00")),
        ("IMEI-T2", py, pm, Decimal("600.00")),
        ("IMEI-T3", cy, cm, Decimal("1200.00")),
    ]:
        p = models.Phone.objects.create(
            name="Phone",
            category=categories["phone"],
            branch=branch,
            imei=imei,
            storage="128",
            color="Black",
            from_by="Supplier",
            cost_price=Decimal("300.00"),
            added_by=users["owner"],
            is_sold=True,
            sell_price=sell,
        )
        set_model_datetime(p, added_at=_aware(month_y, month_m), sold_at=_aware(month_y, month_m))

    comparison = DashboardService.get_phone_dashboard_comparison(branch, cy, cm)

    at = comparison["all_time"]
    # 3 months: 900 + 600 + 1200 = 2700, average = 900
    assert at["total_sold_value"]["average"] == "900.00"
    assert at["total_sold_value"]["current"] == "1200.00"
    assert at["total_sold_value"]["direction"] == "up"


# ---------------------------------------------------------------------------
# Accessory dashboard comparison: previous month
# ---------------------------------------------------------------------------

def test_accessory_comparison_previous_month(branches, users, categories, set_model_datetime):
    branch = branches["main"]
    cy, cm = _current_ym()
    py, pm = _prev_ym()

    acc = models.Accessory.objects.create(
        name="TestAccessory",
        category=categories["accessory"],
        branch=branch,
        unit_cost=Decimal("5.00"),
        stock=100,
        added_by=users["owner"],
        is_active=True,
    )

    sale_prev = models.AccessorySale.objects.create(
        branch=branch,
        accessory=acc,
        sold_by=users["accessory_seller"],
        quantity=3,
        unit_cost=Decimal("5.00"),
        total_cost=Decimal("15.00"),
        total_price=Decimal("30.00"),
        profit=Decimal("15.00"),
        sold_at=_aware(py, pm),
    )
    set_model_datetime(sale_prev, sold_at=_aware(py, pm))

    sale_cur = models.AccessorySale.objects.create(
        branch=branch,
        accessory=acc,
        sold_by=users["accessory_seller"],
        quantity=5,
        unit_cost=Decimal("5.00"),
        total_cost=Decimal("25.00"),
        total_price=Decimal("50.00"),
        profit=Decimal("25.00"),
        sold_at=_aware(cy, cm),
    )
    set_model_datetime(sale_cur, sold_at=_aware(cy, cm))

    comparison = DashboardService.get_accessory_dashboard_comparison(branch, cy, cm)

    pm_cmp = comparison["previous_month"]
    assert pm_cmp["total_sold_value"]["current"] == "50.00"
    assert pm_cmp["total_sold_value"]["previous"] == "30.00"
    assert pm_cmp["total_sold_value"]["direction"] == "up"
    assert pm_cmp["total_quantity_sold"]["current"] == "5.00"
    assert pm_cmp["total_quantity_sold"]["previous"] == "3.00"


def test_accessory_comparison_all_time(branches, users, categories, set_model_datetime):
    branch = branches["main"]
    cy, cm = _current_ym()
    py, pm = _prev_ym()
    ty, tm = _two_months_ago_ym()

    acc = models.Accessory.objects.create(
        name="Acc2",
        category=categories["accessory"],
        branch=branch,
        unit_cost=Decimal("5.00"),
        stock=50,
        added_by=users["owner"],
        is_active=True,
    )

    for idx, (month_y, month_m, total, profit, qty) in enumerate([
        (ty, tm, Decimal("100.00"), Decimal("40.00"), 10),
        (py, pm, Decimal("200.00"), Decimal("80.00"), 20),
        (cy, cm, Decimal("300.00"), Decimal("120.00"), 30),
    ]):
        unit_c = total / qty
        s = models.AccessorySale.objects.create(
            branch=branch,
            accessory=acc,
            sold_by=users["accessory_seller"],
            quantity=qty,
            unit_cost=unit_c,
            total_cost=total - profit,
            total_price=total,
            profit=profit,
            sold_at=_aware(month_y, month_m),
        )
        set_model_datetime(s, sold_at=_aware(month_y, month_m))

    comparison = DashboardService.get_accessory_dashboard_comparison(branch, cy, cm)

    at = comparison["all_time"]
    # 3 months: avg sold_value = (100+200+300)/3 = 200
    assert at["total_sold_value"]["average"] == "200.00"
    assert at["total_sold_value"]["current"] == "300.00"
    assert at["total_sold_value"]["direction"] == "up"


# ---------------------------------------------------------------------------
# Division by zero is safe
# ---------------------------------------------------------------------------

def test_comparison_division_by_zero_safe(branches):
    branch = branches["main"]
    cy, cm = _current_ym()

    # No data at all — should not raise
    comparison = DashboardService.get_phone_dashboard_comparison(branch, cy, cm)
    assert comparison["previous_month"]["total_sold_value"]["direction"] == "neutral"
    assert comparison["all_time"]["total_sold_value"]["direction"] == "neutral"
    assert comparison["all_time"]["total_sold_value"]["percent"] == 0


# ---------------------------------------------------------------------------
# Snapshot path: past month uses snapshot data
# ---------------------------------------------------------------------------

def test_phone_comparison_uses_snapshot_for_previous_month(branches, categories, users, set_model_datetime):
    branch = branches["main"]
    cy, cm = _current_ym()
    py, pm = _prev_ym()

    # Create a snapshot for previous month with known data
    snap_month = date(py, pm, 1)
    models.DashboardSnapshot.objects.create(
        branch=branch,
        month=snap_month,
        phone_data={
            "total_sold_value": "750.00",
            "phone_profit": "250.00",
            "net_profit": "270.00",
            "phones_sold_count": 3,
        },
    )

    # Current month phone sale (live)
    p = models.Phone.objects.create(
        name="Phone",
        category=categories["phone"],
        branch=branch,
        imei="IMEI-SNAP-001",
        storage="128",
        color="Black",
        from_by="Supplier",
        cost_price=Decimal("400.00"),
        added_by=users["owner"],
        is_sold=True,
        sell_price=Decimal("900.00"),
    )
    set_model_datetime(p, added_at=_aware(cy, cm), sold_at=_aware(cy, cm))

    comparison = DashboardService.get_phone_dashboard_comparison(branch, cy, cm)

    pm_cmp = comparison["previous_month"]
    # The comparison should use snapshot data for previous month
    assert pm_cmp["total_sold_value"]["previous"] == "750.00"
    assert pm_cmp["total_sold_value"]["current"] == "900.00"
    assert pm_cmp["total_sold_value"]["direction"] == "up"


# ---------------------------------------------------------------------------
# Current month uses live data (not snapshot)
# ---------------------------------------------------------------------------

def test_current_month_uses_live_data(branches, categories, users, set_model_datetime):
    branch = branches["main"]
    cy, cm = _current_ym()

    # Create a snapshot for current month (should be ignored for current month)
    snap_month = date(cy, cm, 1)
    models.DashboardSnapshot.objects.filter(branch=branch, month=snap_month).delete()
    models.DashboardSnapshot.objects.create(
        branch=branch,
        month=snap_month,
        phone_data={
            "total_sold_value": "99999.00",
            "phone_profit": "99999.00",
            "net_profit": "99999.00",
            "phones_sold_count": 999,
        },
    )

    # Add a real live phone sale
    p = models.Phone.objects.create(
        name="LivePhone",
        category=categories["phone"],
        branch=branch,
        imei="IMEI-LIVE-001",
        storage="64",
        color="Blue",
        from_by="Supplier",
        cost_price=Decimal("200.00"),
        added_by=users["owner"],
        is_sold=True,
        sell_price=Decimal("300.00"),
    )
    set_model_datetime(p, added_at=_aware(cy, cm), sold_at=_aware(cy, cm))

    # Current month data should use live query, not snapshot
    data = DashboardService.get_phone_dashboard(branch, cy, cm)
    # Live data should show 300, not 99999
    assert data["total_sold_value"] == Decimal("300.00")


# ---------------------------------------------------------------------------
# Owner viewing selected staff comparison (phone)
# ---------------------------------------------------------------------------

def test_owner_phone_dashboard_comparison_respects_branch(
    branches, categories, users, set_model_datetime
):
    """Comparison is scoped to the branch, matching how the owner-staff proxy works."""
    branch = branches["main"]
    other_branch = branches["other"]
    cy, cm = _current_ym()
    py, pm = _prev_ym()

    # Sale in main branch (current month)
    p1 = models.Phone.objects.create(
        name="Main",
        category=categories["phone"],
        branch=branch,
        imei="IMEI-MAIN-001",
        storage="128",
        color="Black",
        from_by="S",
        cost_price=Decimal("400.00"),
        added_by=users["owner"],
        is_sold=True,
        sell_price=Decimal("600.00"),
    )
    set_model_datetime(p1, added_at=_aware(cy, cm), sold_at=_aware(cy, cm))

    # Sale in other branch (should not appear in main branch comparison)
    p2 = models.Phone.objects.create(
        name="Other",
        category=categories["phone"],
        branch=other_branch,
        imei="IMEI-OTHER-001",
        storage="128",
        color="White",
        from_by="S",
        cost_price=Decimal("400.00"),
        added_by=users["owner"],
        is_sold=True,
        sell_price=Decimal("1000.00"),
    )
    set_model_datetime(p2, added_at=_aware(cy, cm), sold_at=_aware(cy, cm))

    comparison = DashboardService.get_phone_dashboard_comparison(branch, cy, cm)
    # Only main branch sale: 600.00
    assert comparison["previous_month"]["total_sold_value"]["current"] == "600.00"


# ---------------------------------------------------------------------------
# Owner viewing selected staff comparison (accessory)
# ---------------------------------------------------------------------------

def test_owner_accessory_dashboard_comparison_respects_branch(
    branches, categories, users, set_model_datetime
):
    branch = branches["main"]
    other_branch = branches["other"]
    cy, cm = _current_ym()

    acc_main = models.Accessory.objects.create(
        name="MainAcc",
        category=categories["accessory"],
        branch=branch,
        unit_cost=Decimal("5.00"),
        stock=50,
        added_by=users["owner"],
        is_active=True,
    )
    acc_other = models.Accessory.objects.create(
        name="OtherAcc",
        category=categories["accessory"],
        branch=other_branch,
        unit_cost=Decimal("5.00"),
        stock=50,
        added_by=users["owner"],
        is_active=True,
    )

    s1 = models.AccessorySale.objects.create(
        branch=branch,
        accessory=acc_main,
        sold_by=users["accessory_seller"],
        quantity=2,
        unit_cost=Decimal("10.00"),
        total_cost=Decimal("20.00"),
        total_price=Decimal("40.00"),
        profit=Decimal("20.00"),
        sold_at=_aware(cy, cm),
    )
    set_model_datetime(s1, sold_at=_aware(cy, cm))

    s2 = models.AccessorySale.objects.create(
        branch=other_branch,
        accessory=acc_other,
        sold_by=users["accessory_seller"],
        quantity=10,
        unit_cost=Decimal("10.00"),
        total_cost=Decimal("100.00"),
        total_price=Decimal("200.00"),
        profit=Decimal("100.00"),
        sold_at=_aware(cy, cm),
    )
    set_model_datetime(s2, sold_at=_aware(cy, cm))

    comparison = DashboardService.get_accessory_dashboard_comparison(branch, cy, cm)
    # Only main branch: 40.00
    assert comparison["previous_month"]["total_sold_value"]["current"] == "40.00"


# ---------------------------------------------------------------------------
# Response structure: comparison object is present and well-formed
# ---------------------------------------------------------------------------

def test_phone_comparison_structure(branches):
    branch = branches["main"]
    cy, cm = _current_ym()

    comparison = DashboardService.get_phone_dashboard_comparison(branch, cy, cm)

    assert "previous_month" in comparison
    assert "all_time" in comparison

    for section in ("previous_month", "all_time"):
        for key in ("total_sold_value", "phone_profit", "net_profit", "phones_sold_count"):
            metric = comparison[section][key]
            assert "current" in metric
            assert "diff" in metric
            assert "direction" in metric
            assert metric["direction"] in ("up", "down", "neutral")
            if section == "previous_month":
                assert "previous" in metric
            else:
                assert "average" in metric


def test_accessory_comparison_structure(branches):
    branch = branches["main"]
    cy, cm = _current_ym()

    comparison = DashboardService.get_accessory_dashboard_comparison(branch, cy, cm)

    assert "previous_month" in comparison
    assert "all_time" in comparison

    for section in ("previous_month", "all_time"):
        for key in ("total_sold_value", "accessory_profit", "total_quantity_sold"):
            metric = comparison[section][key]
            assert "current" in metric
            assert "direction" in metric
            assert metric["direction"] in ("up", "down", "neutral")

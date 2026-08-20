from datetime import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from src.core import models
from src.services.dashboard import DashboardService


pytestmark = pytest.mark.django_db


def _current_month_midday():
    today = timezone.localdate().replace(day=1)
    return timezone.make_aware(datetime(today.year, today.month, 15, 10, 0, 0))


def _previous_month_midday():
    today = timezone.localdate().replace(day=1)
    if today.month == 1:
        year = today.year - 1
        month = 12
    else:
        year = today.year
        month = today.month - 1
    return timezone.make_aware(datetime(year, month, 15, 10, 0, 0))


@pytest.mark.parametrize("iteration", range(3))
def test_dashboard_excludes_open_debt_from_previous_month(
    iteration,
    users,
    branches,
    set_model_datetime,
):
    previous_month_dt = _previous_month_midday()
    debt = models.Debt.objects.create(
        branch=branches["main"],
        created_by=users["owner"],
        f_name=f"old-open-{iteration}",
        amount=Decimal("120.00"),
        remaining_amount=Decimal("120.00"),
        direction="WE_GAVE",
        domain=models.Debt.DOMAIN_PHONE,
    )
    set_model_datetime(debt, added_at=previous_month_dt, updated_at=previous_month_dt)

    today = timezone.localdate()
    summary = DashboardService.get_debt_summary(
        branch=branches["main"],
        year=today.year,
        month=today.month,
        role_scope="FULL",
    )

    assert summary["remaining_we_gave"] == Decimal("0.00")
    assert summary["remaining_we_took"] == Decimal("0.00")


@pytest.mark.parametrize("iteration", range(3))
def test_dashboard_uses_remaining_amount_for_current_month_partial_debt(
    iteration,
    users,
    branches,
    set_model_datetime,
):
    current_month_dt = _current_month_midday()
    debt = models.Debt.objects.create(
        branch=branches["main"],
        created_by=users["owner"],
        f_name=f"partial-{iteration}",
        amount=Decimal("100.00"),
        remaining_amount=Decimal("50.00"),
        direction="WE_GAVE",
        domain=models.Debt.DOMAIN_PHONE,
    )
    set_model_datetime(debt, added_at=current_month_dt, updated_at=current_month_dt)
    models.DebtPayment.objects.create(
        debt=debt,
        amount=Decimal("50.00"),
        remaining_balance=Decimal("50.00"),
        paid_by=users["owner"],
        note="partial payment",
    )

    today = timezone.localdate()
    summary = DashboardService.get_debt_summary(
        branch=branches["main"],
        year=today.year,
        month=today.month,
        role_scope="FULL",
    )

    assert summary["total_we_gave"] == Decimal("100.00")
    assert summary["remaining_we_gave"] == Decimal("50.00")


@pytest.mark.parametrize("iteration", range(3))
def test_dashboard_excludes_fully_closed_debt_for_selected_month(
    iteration,
    users,
    branches,
    set_model_datetime,
):
    current_month_dt = _current_month_midday()
    open_debt = models.Debt.objects.create(
        branch=branches["main"],
        created_by=users["owner"],
        f_name=f"open-{iteration}",
        amount=Decimal("40.00"),
        remaining_amount=Decimal("40.00"),
        direction="WE_GAVE",
        domain=models.Debt.DOMAIN_PHONE,
    )
    closed_debt = models.Debt.objects.create(
        branch=branches["main"],
        created_by=users["owner"],
        f_name=f"closed-{iteration}",
        amount=Decimal("70.00"),
        remaining_amount=Decimal("0.00"),
        direction="WE_GAVE",
        domain=models.Debt.DOMAIN_PHONE,
    )
    set_model_datetime(open_debt, added_at=current_month_dt, updated_at=current_month_dt)
    set_model_datetime(closed_debt, added_at=current_month_dt, updated_at=current_month_dt)

    today = timezone.localdate()
    summary = DashboardService.get_debt_summary(
        branch=branches["main"],
        year=today.year,
        month=today.month,
        role_scope="FULL",
    )

    assert summary["total_we_gave"] == Decimal("40.00")
    assert summary["remaining_we_gave"] == Decimal("40.00")


@pytest.mark.parametrize("iteration", range(3))
def test_dashboard_splits_current_month_we_gave_and_we_took_totals(
    iteration,
    users,
    branches,
    set_model_datetime,
):
    current_month_dt = _current_month_midday()
    debt_gave = models.Debt.objects.create(
        branch=branches["main"],
        created_by=users["owner"],
        f_name=f"gave-{iteration}",
        amount=Decimal("30.00"),
        remaining_amount=Decimal("30.00"),
        direction="WE_GAVE",
        domain=models.Debt.DOMAIN_PHONE,
    )
    debt_took = models.Debt.objects.create(
        branch=branches["main"],
        created_by=users["owner"],
        f_name=f"took-{iteration}",
        amount=Decimal("80.00"),
        remaining_amount=Decimal("80.00"),
        direction="WE_TOOK",
        domain=models.Debt.DOMAIN_PHONE,
    )
    set_model_datetime(debt_gave, added_at=current_month_dt, updated_at=current_month_dt)
    set_model_datetime(debt_took, added_at=current_month_dt, updated_at=current_month_dt)

    today = timezone.localdate()
    summary = DashboardService.get_debt_summary(
        branch=branches["main"],
        year=today.year,
        month=today.month,
        role_scope="FULL",
    )

    assert summary["remaining_we_gave"] == Decimal("30.00")
    assert summary["remaining_we_took"] == Decimal("80.00")

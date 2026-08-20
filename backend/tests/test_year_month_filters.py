from datetime import datetime, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from src.core import models
from src.shared.filters import get_available_years


pytestmark = pytest.mark.django_db


def test_get_available_years_returns_distinct_descending_and_current_year_fallback(
    expense_factory,
    set_model_datetime,
):
    current_year = timezone.localdate().year

    first = expense_factory()
    second = expense_factory()

    set_model_datetime(first, added_at=timezone.make_aware(datetime(current_year, 2, 10, 10, 0, 0)))
    set_model_datetime(
        second,
        added_at=timezone.make_aware(datetime(current_year + 1, 1, 10, 10, 0, 0)),
    )

    assert get_available_years(models.Expense.objects.all(), "added_at") == [
        current_year + 1,
        current_year,
    ]
    assert get_available_years(models.Expense.objects.none(), "added_at") == [current_year]


def test_expense_list_defaults_to_current_year_month_and_uses_existing_years(
    client,
    users,
    branches,
    expense_factory,
    set_model_datetime,
):
    current_date = timezone.localdate()
    current_month_dt = timezone.make_aware(
        datetime(current_date.year, current_date.month, 10, 10, 0, 0)
    )
    previous_month_date = current_date.replace(day=1) - timedelta(days=1)
    previous_month_dt = timezone.make_aware(
        datetime(previous_month_date.year, previous_month_date.month, 10, 10, 0, 0)
    )

    current_expense = expense_factory(branch=branches["main"], created_by=users["owner"], note="Current")
    previous_expense = expense_factory(branch=branches["main"], created_by=users["owner"], note="Previous")

    set_model_datetime(current_expense, added_at=current_month_dt, updated_at=current_month_dt)
    set_model_datetime(previous_expense, added_at=previous_month_dt, updated_at=previous_month_dt)

    client.force_login(users["owner"])

    response = client.get(reverse("expense_list"))

    assert response.status_code == 200
    assert response.context["year"] == str(current_date.year)
    assert response.context["month"] == str(current_date.month)
    assert response.context["year_options"] == sorted(
        {current_month_dt.year, previous_month_dt.year},
        reverse=True,
    )

    object_ids = {obj.id for obj in response.context["object_list"]}
    assert current_expense.id in object_ids
    assert previous_expense.id not in object_ids


def test_owner_expense_list_branch_filter_uses_owned_branches(
    client,
    users,
    branches,
    expense_factory,
):
    models.BranchUser.objects.create(
        user=users["owner"],
        branch=branches["other"],
        role=models.BranchUser.ROLE_OWNER,
    )
    main_expense = expense_factory(branch=branches["main"], note="Main Branch Expense")
    other_expense = expense_factory(branch=branches["other"], note="Other Branch Expense")

    client.force_login(users["owner"])

    response = client.get(
        reverse("expense_list"),
        {"branch": str(branches["other"].id)},
    )

    assert response.status_code == 200
    assert response.context["branch"] == str(branches["other"].id)
    object_ids = {obj.id for obj in response.context["object_list"]}
    assert main_expense.id not in object_ids
    assert object_ids == {other_expense.id}

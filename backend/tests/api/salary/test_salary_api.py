from datetime import datetime
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from src.core import models


pytestmark = pytest.mark.django_db


def _paginated_data(response):
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert "count" in data
    assert "next" in data
    assert "previous" in data
    assert "results" in data
    assert len(data["results"]) <= 20
    return data


def _result_ids(response):
    return {item["id"] for item in _paginated_data(response)["results"]}


def _create_user(username):
    return models.User.objects.create_user(username=username, password="pass123")


def _assign_role(user, branch, role):
    return models.BranchUser.objects.create(user=user, branch=branch, role=role)


def test_owner_all_employees_visible(api_client, users, salary_factory):
    salary_phone = salary_factory(employee=users["phone_seller"], note="Phone salary")
    salary_accessory = salary_factory(employee=users["accessory_seller"], note="Accessory salary")

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_salary_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert salary_phone.id in ids
    assert salary_accessory.id in ids


def test_owner_branch_filter_works(api_client, users, branches, salary_factory):
    _assign_role(users["owner"], branches["other"], models.BranchUser.ROLE_OWNER)

    main_salary = salary_factory(note="Main branch salary", branch=branches["main"])
    other_salary = salary_factory(note="Other branch salary", branch=branches["other"])

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_salary_list_create"), {"branch": branches["main"].id})
    assert response.status_code == 200
    assert _result_ids(response) == {main_salary.id}
    assert other_salary.id not in _result_ids(response)


def test_owner_employee_filter_works(api_client, users, salary_factory):
    salary_phone = salary_factory(employee=users["phone_seller"], note="Phone salary")
    salary_accessory = salary_factory(employee=users["accessory_seller"], note="Accessory salary")

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(
        reverse("api_salary_list_create"),
        {"employee": users["phone_seller"].id},
    )
    assert response.status_code == 200
    assert _result_ids(response) == {salary_phone.id}
    assert salary_accessory.id not in _result_ids(response)


def test_seller_only_own_salary(api_client, users, salary_factory):
    own_salary = salary_factory(employee=users["phone_seller"], note="Own salary")
    other_salary = salary_factory(employee=users["accessory_seller"], note="Other salary")

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_salary_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert own_salary.id in ids
    assert other_salary.id not in ids


def test_seller_cannot_see_other_user_salary(api_client, users, salary_factory):
    salary_factory(employee=users["accessory_seller"], note="Other salary")
    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_salary_list_create"))
    assert response.status_code == 200
    assert response.json()["data"]["count"] == 0


def test_seller_same_branch_salary_not_visible(api_client, users, branches, salary_factory):
    other_phone_seller = _create_user("second_phone_seller")
    _assign_role(other_phone_seller, branches["main"], models.BranchUser.ROLE_PHONE_SELLER)
    other_salary = salary_factory(employee=other_phone_seller, note="Other phone seller salary")
    own_salary = salary_factory(employee=users["phone_seller"], note="Own salary")

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_salary_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert own_salary.id in ids
    assert other_salary.id not in ids


def test_seller_default_list_returns_current_year(api_client, users, salary_factory, set_model_datetime):
    """Seller list with no params returns current-year salaries (not just current month)."""
    year = timezone.localdate().year
    if timezone.localdate().month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = timezone.localdate().month - 1

    jan_salary = salary_factory(employee=users["phone_seller"], note="Jan salary")
    prev_salary = salary_factory(employee=users["phone_seller"], note="Prev month salary")
    last_year_salary = salary_factory(employee=users["phone_seller"], note="Last year salary")

    jan_dt = timezone.make_aware(datetime(year, 1, 10, 10, 0, 0))
    prev_dt = timezone.make_aware(datetime(prev_year, prev_month, 10, 10, 0, 0))
    last_year_dt = timezone.make_aware(datetime(year - 1, 6, 10, 10, 0, 0))

    set_model_datetime(jan_salary, added_at=jan_dt, updated_at=jan_dt)
    set_model_datetime(prev_salary, added_at=prev_dt, updated_at=prev_dt)
    set_model_datetime(last_year_salary, added_at=last_year_dt, updated_at=last_year_dt)

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_salary_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert jan_salary.id in ids
    assert prev_salary.id in ids
    assert last_year_salary.id not in ids


def test_seller_yearly_filter_works(api_client, users, salary_factory, set_model_datetime):
    year = timezone.localdate().year
    january = timezone.make_aware(datetime(year, 1, 10, 10, 0, 0))
    february = timezone.make_aware(datetime(year, 2, 10, 10, 0, 0))

    jan_salary = salary_factory(employee=users["phone_seller"], note="Jan salary")
    feb_salary = salary_factory(employee=users["phone_seller"], note="Feb salary")
    set_model_datetime(jan_salary, added_at=january, updated_at=january)
    set_model_datetime(feb_salary, added_at=february, updated_at=february)

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_salary_list_create"), {"year": str(year)})
    assert response.status_code == 200
    ids = _result_ids(response)
    assert jan_salary.id in ids
    assert feb_salary.id in ids


def test_current_month_default_works(api_client, users, salary_factory, set_model_datetime, time_points):
    current_salary = salary_factory(note="Current salary")
    previous_salary = salary_factory(note="Previous salary")
    set_model_datetime(current_salary, added_at=time_points["current"], updated_at=time_points["current"])
    set_model_datetime(previous_salary, added_at=time_points["previous"], updated_at=time_points["previous"])

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_salary_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert current_salary.id in ids
    assert previous_salary.id not in ids


def test_owner_add_salary_for_phone_seller(api_client, users, branches):
    """Owner can create salary for owned branch phone seller."""
    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_salary_list_create"),
        {"employee": users["phone_seller"].id, "amount": "75.00", "note": "Phone salary"},
        format="json",
    )
    assert response.status_code == 201
    salary = models.Salary.objects.get(note="Phone salary")
    assert salary.employee_id == users["phone_seller"].id
    assert salary.created_by_id == users["owner"].id
    assert salary.amount == Decimal("75.00")


def test_owner_add_salary_for_accessory_seller(api_client, users, branches):
    """Owner can create salary for owned branch accessory seller."""
    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_salary_list_create"),
        {"employee": users["accessory_seller"].id, "amount": "60.00", "note": "Accessory salary"},
        format="json",
    )
    assert response.status_code == 201
    salary = models.Salary.objects.get(note="Accessory salary")
    assert salary.employee_id == users["accessory_seller"].id
    assert salary.amount == Decimal("60.00")


def test_owner_add_salary_works(api_client, users, branches):
    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_salary_list_create"),
        {"employee": users["phone_seller"].id, "amount": "75.00", "note": "Salary"},
        format="json",
    )
    assert response.status_code == 201
    salary = models.Salary.objects.get(note="Salary")
    assert salary.employee_id == users["phone_seller"].id
    assert salary.created_by_id == users["owner"].id
    assert salary.amount == Decimal("75.00")


def test_owner_cannot_create_salary_for_user_outside_owned_branches(api_client, users):
    """Owner cannot create salary for a user not in any owned branch."""
    outsider = models.User.objects.create_user(username="outsider_salary", password="pass123")
    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_salary_list_create"),
        {"employee": outsider.id, "amount": "50.00", "note": "Outsider salary"},
        format="json",
    )
    assert response.status_code in (400, 403)


def test_owner_cannot_create_salary_for_non_seller(api_client, users, branches):
    """Owner cannot create salary for a non-seller role (e.g., owner of same branch)."""
    second_owner = models.User.objects.create_user(username="second_owner_sal", password="pass123")
    models.BranchUser.objects.create(
        user=second_owner, branch=branches["main"], role=models.BranchUser.ROLE_OWNER
    )
    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_salary_list_create"),
        {"employee": second_owner.id, "amount": "50.00", "note": "Non-seller salary"},
        format="json",
    )
    assert response.status_code in (400, 403)


def test_phone_seller_salary_affects_phone_capital_only(api_client, users, branches):
    """Salary for a phone seller subtracts from PhoneCapital, not AccessoryCapital."""
    month_start = timezone.localdate().replace(day=1)
    phone_capital = models.PhoneCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("500.00"),
        current_balance=Decimal("500.00"),
    )
    accessory_capital = models.AccessoryCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("300.00"),
        current_balance=Decimal("300.00"),
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_salary_list_create"),
        {"employee": users["phone_seller"].id, "amount": "100.00", "note": "Phone sal capital"},
        format="json",
    )
    assert response.status_code == 201

    phone_capital.refresh_from_db()
    accessory_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("400.00")
    assert accessory_capital.current_balance == Decimal("300.00")


def test_accessory_seller_salary_affects_accessory_capital_only(api_client, users, branches):
    """Salary for an accessory seller subtracts from AccessoryCapital, not PhoneCapital."""
    month_start = timezone.localdate().replace(day=1)
    phone_capital = models.PhoneCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("500.00"),
        current_balance=Decimal("500.00"),
    )
    accessory_capital = models.AccessoryCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("300.00"),
        current_balance=Decimal("300.00"),
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_salary_list_create"),
        {"employee": users["accessory_seller"].id, "amount": "80.00", "note": "Acc sal capital"},
        format="json",
    )
    assert response.status_code == 201

    phone_capital.refresh_from_db()
    accessory_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("500.00")
    assert accessory_capital.current_balance == Decimal("220.00")


def test_seller_cannot_add_salary(api_client, users):
    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.post(
        reverse("api_salary_list_create"),
        {"employee": users["phone_seller"].id, "amount": "30.00"},
        format="json",
    )
    assert response.status_code == 403


def test_owner_delete_salary_works(api_client, users, salary_factory):
    salary = salary_factory(note="To delete")
    api_client.force_authenticate(user=users["owner"])
    response = api_client.delete(reverse("api_salary_delete", args=[salary.id]))
    assert response.status_code == 200
    assert models.Salary.all_objects.get(pk=salary.id).is_deleted is True


def test_salary_delete_past_month_blocked(
    api_client,
    users,
    branches,
    salary_factory,
    set_model_datetime,
    time_points,
):
    """Owner cannot delete a salary from a previous month."""
    salary = salary_factory(note="Past salary", branch=branches["main"])
    set_model_datetime(salary, added_at=time_points["previous"], updated_at=time_points["previous"])

    api_client.force_authenticate(user=users["owner"])
    response = api_client.delete(reverse("api_salary_delete", args=[salary.id]))
    assert response.status_code == 400
    assert models.Salary.all_objects.get(pk=salary.id).is_deleted is False


def test_seller_cannot_delete_salary(api_client, users, salary_factory):
    salary = salary_factory(note="To delete")
    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.delete(reverse("api_salary_delete", args=[salary.id]))
    assert response.status_code == 403

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


def test_phone_seller_only_sees_own_branch_phone_expenses(
    api_client,
    users,
    branches,
    expense_factory,
):
    phone_expense = expense_factory(
        note="Phone expense",
        created_by=users["phone_seller"],
        branch=branches["main"],
    )
    accessory_expense = expense_factory(
        note="Accessory expense",
        created_by=users["accessory_seller"],
        branch=branches["main"],
        type="EMPLOYEE_EXPENSE",
    )

    other_phone_seller = _create_user("other_branch_phone_seller")
    _assign_role(other_phone_seller, branches["other"], models.BranchUser.ROLE_PHONE_SELLER)
    other_branch_expense = expense_factory(
        note="Other branch phone expense",
        created_by=other_phone_seller,
        branch=branches["other"],
    )

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_expense_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert phone_expense.id in ids
    assert accessory_expense.id not in ids
    assert other_branch_expense.id not in ids


def test_phone_seller_sees_same_branch_phone_seller_expenses(
    api_client,
    users,
    branches,
    expense_factory,
):
    """Phone seller sees all phone-domain expenses in same branch, not only own."""
    peer_phone_seller = _create_user("peer_phone_seller_list")
    _assign_role(peer_phone_seller, branches["main"], models.BranchUser.ROLE_PHONE_SELLER)

    own_expense = expense_factory(
        note="Own phone expense",
        created_by=users["phone_seller"],
        branch=branches["main"],
    )
    peer_expense = expense_factory(
        note="Peer phone expense",
        created_by=peer_phone_seller,
        branch=branches["main"],
    )
    accessory_expense = expense_factory(
        note="Accessory expense",
        created_by=users["accessory_seller"],
        branch=branches["main"],
        type="EMPLOYEE_EXPENSE",
    )

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_expense_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert own_expense.id in ids
    assert peer_expense.id in ids
    assert accessory_expense.id not in ids


def test_accessory_seller_cannot_see_phone_expenses(api_client, users, branches, expense_factory):
    phone_expense = expense_factory(
        note="Phone expense",
        created_by=users["phone_seller"],
        branch=branches["main"],
    )
    accessory_expense = expense_factory(
        note="Accessory expense",
        created_by=users["accessory_seller"],
        branch=branches["main"],
        type="EMPLOYEE_EXPENSE",
    )

    api_client.force_authenticate(user=users["accessory_seller"])
    response = api_client.get(reverse("api_expense_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert accessory_expense.id in ids
    assert phone_expense.id not in ids


def test_accessory_seller_sees_same_branch_accessory_seller_expenses(
    api_client,
    users,
    branches,
    expense_factory,
):
    """Accessory seller sees all accessory-domain expenses in same branch."""
    peer_accessory_seller = _create_user("peer_accessory_seller_list")
    _assign_role(peer_accessory_seller, branches["main"], models.BranchUser.ROLE_ACCESSORY_SELLER)

    own_expense = expense_factory(
        note="Own accessory expense",
        created_by=users["accessory_seller"],
        branch=branches["main"],
        type="EMPLOYEE_EXPENSE",
    )
    peer_expense = expense_factory(
        note="Peer accessory expense",
        created_by=peer_accessory_seller,
        branch=branches["main"],
        type="EMPLOYEE_EXPENSE",
    )
    phone_expense = expense_factory(
        note="Phone expense",
        created_by=users["phone_seller"],
        branch=branches["main"],
    )

    api_client.force_authenticate(user=users["accessory_seller"])
    response = api_client.get(reverse("api_expense_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert own_expense.id in ids
    assert peer_expense.id in ids
    assert phone_expense.id not in ids


def test_accessory_seller_only_sees_own_branch_accessory_expenses(
    api_client,
    users,
    branches,
    expense_factory,
):
    own_expense = expense_factory(
        note="Own accessory expense",
        created_by=users["accessory_seller"],
        branch=branches["main"],
        type="EMPLOYEE_EXPENSE",
    )

    other_accessory_seller = _create_user("other_branch_accessory_seller")
    _assign_role(other_accessory_seller, branches["other"], models.BranchUser.ROLE_ACCESSORY_SELLER)
    other_branch_expense = expense_factory(
        note="Other branch accessory expense",
        created_by=other_accessory_seller,
        branch=branches["other"],
        type="EMPLOYEE_EXPENSE",
    )

    api_client.force_authenticate(user=users["accessory_seller"])
    response = api_client.get(reverse("api_expense_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert own_expense.id in ids
    assert other_branch_expense.id not in ids


def test_owner_sees_all_branch_expenses(api_client, users, branches, expense_factory):
    _assign_role(users["owner"], branches["other"], models.BranchUser.ROLE_OWNER)

    main_expense = expense_factory(note="Main expense", branch=branches["main"])
    other_expense = expense_factory(note="Other expense", branch=branches["other"])

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_expense_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert main_expense.id in ids
    assert other_expense.id in ids


def test_owner_branch_filter_works(api_client, users, branches, expense_factory):
    _assign_role(users["owner"], branches["other"], models.BranchUser.ROLE_OWNER)

    main_expense = expense_factory(note="Main expense", branch=branches["main"])
    other_expense = expense_factory(note="Other expense", branch=branches["other"])

    api_client.force_authenticate(user=users["owner"])
    main_response = api_client.get(
        reverse("api_expense_list_create"),
        {"branch": branches["main"].id},
    )
    assert main_response.status_code == 200
    assert _result_ids(main_response) == {main_expense.id}

    other_response = api_client.get(
        reverse("api_expense_list_create"),
        {"branch": branches["other"].id},
    )
    assert other_response.status_code == 200
    assert _result_ids(other_response) == {other_expense.id}


def test_owner_employee_filter_works(api_client, users, expense_factory):
    phone_expense = expense_factory(note="Phone expense", created_by=users["phone_seller"])
    accessory_expense = expense_factory(
        note="Accessory expense",
        created_by=users["accessory_seller"],
        type="EMPLOYEE_EXPENSE",
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(
        reverse("api_expense_list_create"),
        {"employee": users["phone_seller"].id},
    )
    assert response.status_code == 200
    assert _result_ids(response) == {phone_expense.id}
    assert accessory_expense.id not in _result_ids(response)


def test_current_month_default_filter_works(
    api_client,
    users,
    expense_factory,
    set_model_datetime,
    time_points,
):
    current_expense = expense_factory(note="Current expense")
    previous_expense = expense_factory(note="Previous expense")
    set_model_datetime(current_expense, added_at=time_points["current"], updated_at=time_points["current"])
    set_model_datetime(
        previous_expense,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_expense_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert current_expense.id in ids
    assert previous_expense.id not in ids


def test_type_filter_works(api_client, users, expense_factory):
    shop = expense_factory(note="Shop expense", type="SHOP_EXPENSE")
    employee = expense_factory(note="Employee expense", type="EMPLOYEE_EXPENSE")

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_expense_list_create"), {"type": "SHOP_EXPENSE"})
    assert response.status_code == 200
    assert _result_ids(response) == {shop.id}
    assert employee.id not in _result_ids(response)


def test_add_expense_only_sellers(api_client, users, branches):
    api_client.force_authenticate(user=users["phone_seller"])
    phone_response = api_client.post(
        reverse("api_expense_list_create"),
        {
            "branch": branches["other"].id,
            "type": "SHOP_EXPENSE",
            "amount": "15.00",
            "note": "Phone seller expense",
        },
        format="json",
    )
    assert phone_response.status_code == 201
    phone_expense = models.Expense.objects.get(pk=phone_response.json()["data"]["id"])
    assert phone_expense.branch_id == branches["main"].id
    assert phone_expense.created_by_id == users["phone_seller"].id
    assert phone_expense.capital_type == models.Expense.CAPITAL_TYPE_PHONE

    api_client.force_authenticate(user=users["accessory_seller"])
    accessory_response = api_client.post(
        reverse("api_expense_list_create"),
        {
            "type": "EMPLOYEE_EXPENSE",
            "amount": "10.00",
            "note": "Accessory seller expense",
        },
        format="json",
    )
    assert accessory_response.status_code == 201
    accessory_expense = models.Expense.objects.get(pk=accessory_response.json()["data"]["id"])
    assert accessory_expense.branch_id == branches["main"].id
    assert accessory_expense.created_by_id == users["accessory_seller"].id
    assert accessory_expense.capital_type == models.Expense.CAPITAL_TYPE_ACCESSORY


def test_owner_cannot_add_expense(api_client, users):
    api_client.force_authenticate(user=users["owner"])
    response = api_client.post(
        reverse("api_expense_list_create"),
        {
            "type": "SHOP_EXPENSE",
            "amount": "10.00",
            "note": "Owner expense",
        },
        format="json",
    )
    assert response.status_code == 403


def test_owner_can_delete_current_month_expense_in_owned_branch(
    api_client,
    users,
    branches,
    expense_factory,
):
    """Owner can delete current-month expense in an owned branch."""
    expense = expense_factory(
        note="Owner deletable",
        created_by=users["phone_seller"],
        branch=branches["main"],
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.delete(reverse("api_expense_delete", args=[expense.id]))
    assert response.status_code == 200
    assert models.Expense.all_objects.get(pk=expense.id).is_deleted is True


def test_owner_cannot_delete_expense_in_non_owned_branch(
    api_client,
    users,
    branches,
    expense_factory,
):
    """Owner cannot delete expense in a branch they don't own."""
    other_owner = _create_user("other_owner_exp")
    other_branch = models.Branch.objects.create(name="Other Owner Branch", owner=other_owner)
    _assign_role(other_owner, other_branch, models.BranchUser.ROLE_OWNER)
    other_seller = _create_user("other_seller_exp")
    _assign_role(other_seller, other_branch, models.BranchUser.ROLE_PHONE_SELLER)

    other_expense = expense_factory(
        note="Other owner expense",
        created_by=other_seller,
        branch=other_branch,
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.delete(reverse("api_expense_delete", args=[other_expense.id]))
    assert response.status_code == 403
    assert models.Expense.all_objects.get(pk=other_expense.id).is_deleted is False


def test_past_month_expense_delete_blocked(
    api_client,
    users,
    branches,
    expense_factory,
    set_model_datetime,
    time_points,
):
    """Past-month expense delete is blocked for both sellers and owners."""
    previous_expense = expense_factory(
        note="Previous delete",
        created_by=users["phone_seller"],
        branch=branches["main"],
    )
    previous_expense.capital_type = models.Expense.CAPITAL_TYPE_PHONE
    previous_expense.save(update_fields=["capital_type", "updated_at"])
    set_model_datetime(
        previous_expense,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    # Seller cannot delete past-month expense
    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.delete(reverse("api_expense_delete", args=[previous_expense.id]))
    assert response.status_code == 400
    assert models.Expense.all_objects.get(pk=previous_expense.id).is_deleted is False

    # Owner also cannot delete past-month expense
    api_client.force_authenticate(user=users["owner"])
    response = api_client.delete(reverse("api_expense_delete", args=[previous_expense.id]))
    assert response.status_code == 400
    assert models.Expense.all_objects.get(pk=previous_expense.id).is_deleted is False


def test_expense_delete_restores_correct_capital(
    api_client,
    users,
    branches,
    expense_factory,
):
    """Deleting an expense restores balance to the correct capital only."""
    month_start = timezone.localdate().replace(day=1)
    phone_capital = models.PhoneCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("500.00"),
        current_balance=Decimal("400.00"),
    )
    accessory_capital = models.AccessoryCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("200.00"),
        current_balance=Decimal("150.00"),
    )

    expense = expense_factory(
        note="Phone expense to delete",
        created_by=users["phone_seller"],
        branch=branches["main"],
        amount=Decimal("30.00"),
    )
    expense.capital_type = models.Expense.CAPITAL_TYPE_PHONE
    expense.save(update_fields=["capital_type", "updated_at"])

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.delete(reverse("api_expense_delete", args=[expense.id]))
    assert response.status_code == 200

    phone_capital.refresh_from_db()
    accessory_capital.refresh_from_db()
    assert phone_capital.current_balance == Decimal("430.00")
    assert accessory_capital.current_balance == Decimal("150.00")


def test_delete_permission_enforced(
    api_client,
    users,
    branches,
    expense_factory,
    set_model_datetime,
    time_points,
):
    expense = expense_factory(note="To delete", created_by=users["phone_seller"], branch=branches["main"])

    # Accessory seller cannot delete phone seller expense
    api_client.force_authenticate(user=users["accessory_seller"])
    assert api_client.delete(reverse("api_expense_delete", args=[expense.id])).status_code == 403

    # Phone seller can delete own current-month expense
    api_client.force_authenticate(user=users["phone_seller"])
    ok_response = api_client.delete(reverse("api_expense_delete", args=[expense.id]))
    assert ok_response.status_code == 200
    assert models.Expense.all_objects.get(pk=expense.id).is_deleted is True

    # Past-month delete is blocked (returns 400)
    previous_expense = expense_factory(
        note="Previous delete",
        created_by=users["phone_seller"],
        branch=branches["main"],
    )
    previous_expense.capital_type = models.Expense.CAPITAL_TYPE_PHONE
    previous_expense.save(update_fields=["capital_type", "updated_at"])
    set_model_datetime(
        previous_expense,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["phone_seller"])
    previous_delete = api_client.delete(reverse("api_expense_delete", args=[previous_expense.id]))
    assert previous_delete.status_code == 400
    assert models.Expense.all_objects.get(pk=previous_expense.id).is_deleted is False

    # Owner can delete current-month expense in owned branch
    owner_deletable = expense_factory(
        note="Owner delete",
        created_by=users["phone_seller"],
        branch=branches["main"],
    )
    api_client.force_authenticate(user=users["owner"])
    owner_delete = api_client.delete(reverse("api_expense_delete", args=[owner_deletable.id]))
    assert owner_delete.status_code == 200
    assert models.Expense.all_objects.get(pk=owner_deletable.id).is_deleted is True


def test_branch_isolation_works(api_client, users, branches, expense_factory):
    main_expense = expense_factory(note="Main expense", branch=branches["main"])

    other_owner = _create_user("other_owner")
    other_branch = models.Branch.objects.create(name="Other owner branch", owner=other_owner)
    _assign_role(other_owner, other_branch, models.BranchUser.ROLE_OWNER)
    other_seller = _create_user("other_phone_seller")
    _assign_role(other_seller, other_branch, models.BranchUser.ROLE_PHONE_SELLER)
    other_branch_expense = expense_factory(
        note="Other branch expense",
        branch=other_branch,
        created_by=other_seller,
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_expense_list_create"))
    assert response.status_code == 200
    ids = _result_ids(response)
    assert main_expense.id in ids
    assert other_branch_expense.id not in ids


def test_create_never_affects_other_branch_capital(api_client, users, branches):
    """Creating an expense only subtracts from the correct branch capital."""
    month_start = timezone.localdate().replace(day=1)
    main_phone_capital = models.PhoneCapital.objects.create(
        branch=branches["main"],
        month=month_start,
        invested_amount=Decimal("300.00"),
        current_balance=Decimal("300.00"),
    )
    other_phone_capital = models.PhoneCapital.objects.create(
        branch=branches["other"],
        month=month_start,
        invested_amount=Decimal("100.00"),
        current_balance=Decimal("100.00"),
    )

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.post(
        reverse("api_expense_list_create"),
        {"type": "SHOP_EXPENSE", "amount": "20.00", "note": "Capital test"},
        format="json",
    )
    assert response.status_code == 201

    main_phone_capital.refresh_from_db()
    other_phone_capital.refresh_from_db()
    assert main_phone_capital.current_balance == Decimal("280.00")
    assert other_phone_capital.current_balance == Decimal("100.00")

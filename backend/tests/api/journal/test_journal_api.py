from datetime import timedelta

import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


def test_owner_sees_own_and_branch_user_journals(
    api_client,
    users,
    branches,
    journal_factory,
):
    owner_entry = journal_factory(user=users["owner"], model_name="expense", object_repr="Owner action")
    seller_entry = journal_factory(
        user=users["phone_seller"],
        model_name="phone",
        object_repr="Seller action",
    )
    other_branch_entry = journal_factory(
        branch=branches["other"],
        user=users["outsider"],
        model_name="phone",
        object_repr="Other branch action",
    )

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_journal_list"))

    assert response.status_code == 200
    result_ids = {item["id"] for item in response.json()["data"]["results"]}
    assert owner_entry.id in result_ids
    assert seller_entry.id in result_ids
    assert other_branch_entry.id not in result_ids


def test_seller_sees_only_own_records(api_client, users, journal_factory):
    own_entry = journal_factory(
        user=users["phone_seller"],
        model_name="extra_profit",
        object_repr="Own seller journal",
    )
    other_user_entry = journal_factory(
        user=users["owner"],
        model_name="extra_profit",
        object_repr="Owner journal",
    )
    blocked_model_entry = journal_factory(
        user=users["phone_seller"],
        model_name="salary",
        object_repr="Blocked model",
    )

    api_client.force_authenticate(user=users["phone_seller"])
    response = api_client.get(reverse("api_journal_list"))

    assert response.status_code == 200
    result_ids = {item["id"] for item in response.json()["data"]["results"]}
    assert own_entry.id in result_ids
    assert other_user_entry.id not in result_ids
    assert blocked_model_entry.id not in result_ids


def test_admin_sees_all_and_can_filter_by_user(api_client, users, branches, journal_factory):
    admin_entry = journal_factory(user=users["admin"], branch=branches["other"], object_repr="Admin view 1")
    seller_entry = journal_factory(user=users["phone_seller"], object_repr="Admin view 2")

    api_client.force_authenticate(user=users["admin"])

    response = api_client.get(reverse("api_journal_list"))
    assert response.status_code == 200
    result_ids = {item["id"] for item in response.json()["data"]["results"]}
    assert admin_entry.id in result_ids
    assert seller_entry.id in result_ids

    filtered = api_client.get(reverse("api_journal_list"), {"user": users["phone_seller"].id})
    filtered_ids = {item["id"] for item in filtered.json()["data"]["results"]}
    assert seller_entry.id in filtered_ids
    assert admin_entry.id not in filtered_ids


def test_journal_month_year_filter_works(
    api_client,
    users,
    journal_factory,
    set_model_datetime,
    time_points,
):
    current_entry = journal_factory(object_repr="Current journal")
    previous_entry = journal_factory(object_repr="Previous journal")

    set_model_datetime(
        current_entry,
        added_at=time_points["current"] + timedelta(hours=1),
        updated_at=time_points["current"] + timedelta(hours=1),
    )
    set_model_datetime(
        previous_entry,
        added_at=time_points["previous"],
        updated_at=time_points["previous"],
    )

    api_client.force_authenticate(user=users["admin"])

    default_response = api_client.get(reverse("api_journal_list"))
    default_ids = {item["id"] for item in default_response.json()["data"]["results"]}
    assert current_entry.id in default_ids
    assert previous_entry.id in default_ids

    previous_response = api_client.get(
        reverse("api_journal_list"),
        {
            "year": str(time_points["previous"].year),
            "month": str(time_points["previous"].month),
        },
    )
    previous_ids = {item["id"] for item in previous_response.json()["data"]["results"]}
    assert previous_entry.id in previous_ids
    assert current_entry.id not in previous_ids


def test_journal_no_cross_branch_leak_for_owner(api_client, users, branches, journal_factory):
    visible = journal_factory(branch=branches["main"], user=users["phone_seller"], object_repr="Visible")
    hidden = journal_factory(branch=branches["other"], user=users["outsider"], object_repr="Hidden")

    api_client.force_authenticate(user=users["owner"])
    response = api_client.get(reverse("api_journal_list"))

    assert response.status_code == 200
    result_ids = {item["id"] for item in response.json()["data"]["results"]}
    assert visible.id in result_ids
    assert hidden.id not in result_ids


def test_cashier_cannot_access_journal(api_client, users):
    api_client.force_authenticate(user=users["cashier"])
    response = api_client.get(reverse("api_journal_list"))
    assert response.status_code == 403

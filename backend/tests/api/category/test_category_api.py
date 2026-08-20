import pytest
from django.urls import reverse

from src.core import models


pytestmark = pytest.mark.django_db


def test_phone_category_list_works_for_admin(api_client, users):
    first = models.PhoneCategory.objects.create(name="Flagship")
    second = models.PhoneCategory.objects.create(name="Budget")

    api_client.force_authenticate(user=users["admin"])
    response = api_client.get(reverse("api_phone_category_list"))

    assert response.status_code == 200
    payload = response.json()["data"]
    result_ids = {item["id"] for item in payload["results"]}
    assert first.id in result_ids
    assert second.id in result_ids


def test_accessory_category_list_works_for_admin(api_client, users):
    first = models.AccessoryCategory.objects.create(name="Cases")
    second = models.AccessoryCategory.objects.create(name="Chargers")

    api_client.force_authenticate(user=users["admin"])
    response = api_client.get(reverse("api_accessory_category_list"))

    assert response.status_code == 200
    payload = response.json()["data"]
    result_ids = {item["id"] for item in payload["results"]}
    assert first.id in result_ids
    assert second.id in result_ids


def test_category_endpoints_are_superadmin_only(api_client, users, categories):
    api_client.force_authenticate(user=users["owner"])
    phone_response = api_client.get(reverse("api_phone_category_list"))
    accessory_response = api_client.get(reverse("api_accessory_category_list"))

    assert phone_response.status_code == 403
    assert accessory_response.status_code == 403

    api_client.force_authenticate(user=users["phone_seller"])
    seller_phone = api_client.get(reverse("api_phone_category_list"))
    seller_accessory = api_client.get(reverse("api_accessory_category_list"))

    assert seller_phone.status_code == 403
    assert seller_accessory.status_code == 403


def test_category_payload_matches_db(api_client, users):
    category = models.PhoneCategory.objects.create(name="Camera Phones")

    api_client.force_authenticate(user=users["admin"])
    response = api_client.get(reverse("api_phone_category_list"))

    assert response.status_code == 200
    row = next(item for item in response.json()["data"]["results"] if item["id"] == category.id)
    assert row["name"] == category.name
    assert "added_at" in row

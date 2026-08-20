"""Public contact-request endpoint — ochiq, autentifikatsiyasiz yozuv nuqtasi."""

import sys

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

import src.core.models as models
from src.api.serializers.public import normalize_uz_phone


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def _fake_requests_module(post):
    """`requests` o'rniga qo'yiladigan minimal soxta modul.

    Notifier `requests`ni funksiya ichida import qiladi, shuning uchun
    sys.modules'ga qo'yish yetarli. Bu testlarni haqiqiy `requests`
    paketining o'rnatilgan-o'rnatilmaganidan mustaqil qiladi.
    """
    import types

    module = types.ModuleType("requests")
    module.post = post
    return module


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Xavfsizlik to'ri: birorta test ham haqiqiy HTTP chaqiruv qilmasin.

    Standart sozlamalarda TELEGRAM_NOTIFICATIONS_ENABLED=False va
    TELEGRAM_SUPPORT_CHAT_ID bo'sh, shuning uchun notifier baribir jimgina
    o'tkazib yuboradi — bu shunchaki kafolat.
    """

    def _boom(*args, **kwargs):
        raise AssertionError("Testda haqiqiy tarmoq chaqiruvi bo'ldi")

    monkeypatch.setitem(sys.modules, "requests", _fake_requests_module(_boom))


def _url():
    return reverse("api_public_contact_request")


def _post(api_client, data=None, ip="127.0.0.1"):
    payload = {"phone": "+998901234567", "region": "andijon"}
    if data is not None:
        payload = data
    return api_client.post(_url(), payload, format="json", REMOTE_ADDR=ip)


def _set_rate(monkeypatch, scope, rate):
    """Throttle tezligini o'zgartiradi.

    ``override_settings(REST_FRAMEWORK=...)`` bu yerda ishlamaydi:
    ``SimpleRateThrottle.THROTTLE_RATES`` import vaqtida bog'lanadi.
    """
    from rest_framework.throttling import SimpleRateThrottle

    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, scope, rate)


# ---------------------------------------------------------------- happy path


def test_valid_request_creates_support_request(api_client):
    response = _post(api_client)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert "qabul qilindi" in body["data"]["message"]

    request_obj = models.SupportRequest.objects.get()
    assert request_obj.request_type == models.SupportRequest.RequestType.CONTACT
    assert request_obj.source == models.SupportRequest.Source.PUBLIC_APP
    assert request_obj.phone == "+998901234567"
    assert request_obj.contact_region == "andijon"
    assert request_obj.user is None
    assert request_obj.status == models.SupportRequest.Status.NEW


def test_anonymous_access_without_any_auth_header(api_client):
    """Hech qanday Authorization/X-Key sarlavhasisiz ishlaydi."""
    response = _post(api_client)
    assert response.status_code == 201


def test_stale_token_does_not_break_the_call(api_client):
    """Eskirgan JWT qolgan qurilmada ham 201 — view autentifikatsiyani o'qimaydi."""
    api_client.credentials(HTTP_AUTHORIZATION="Bearer eskirgan.token.qiymati")
    response = _post(api_client)
    assert response.status_code == 201
    assert models.SupportRequest.objects.get().user is None


def test_message_contains_region_and_phone(api_client):
    """CRM shablonlari faqat message/phone ko'rsatadi — viloyat matnda bo'lsin."""
    _post(api_client)
    request_obj = models.SupportRequest.objects.get()
    assert "Andijon" in request_obj.message
    assert "+998901234567" in request_obj.message


def test_initial_message_is_created_as_external(api_client):
    _post(api_client)
    request_obj = models.SupportRequest.objects.get()
    message = request_obj.messages.get()
    assert message.sender is None
    assert message.sender_type == models.SupportRequestMessage.SenderType.EXTERNAL


def test_telegram_notification_is_triggered(api_client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "src.services.support.telegram.SupportTelegramNotifier.send_contact_request",
        lambda self, support_request: sent.append(support_request) or True,
    )
    _post(api_client)
    assert len(sent) == 1
    assert sent[0].source == models.SupportRequest.Source.PUBLIC_APP
    assert sent[0].contact_region == "andijon"


# ------------------------------------------------------------------ phone


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("+998901234567", "+998901234567"),
        ("998901234567", "+998901234567"),
        ("901234567", "+998901234567"),
        ("+998 90 123 45 67", "+998901234567"),
        ("+998-90-123-45-67", "+998901234567"),
        ("(90) 123-45-67", "+998901234567"),
    ],
)
def test_phone_formats_normalize_to_one_form(api_client, raw, expected):
    response = _post(api_client, {"phone": raw, "region": "andijon"})
    assert response.status_code == 201, response.json()
    assert models.SupportRequest.objects.get().phone == expected


@pytest.mark.parametrize(
    "raw",
    [
        "12345",
        "+7 900 123 45 67",
        "+9989012345678",
        "abcdefghi",
        "+998 0 123 45 67",
        "",
        "998012345678",  # mavjud bo'lmagan kod "01"
        "+998111234567",  # "11" — kod emas
        "+998641234567",  # "64" — kod emas
    ],
)
def test_invalid_phone_returns_400_in_uzbek(api_client, raw):
    response = _post(api_client, {"phone": raw, "region": "andijon"})
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "phone" in body["error"]
    assert models.SupportRequest.objects.count() == 0


def test_normalize_uz_phone_unit():
    assert normalize_uz_phone("901234567") == "+998901234567"
    assert normalize_uz_phone("+998 33 123 45 67") == "+998331234567"
    assert normalize_uz_phone(None) is None
    assert normalize_uz_phone("998012345678") is None


def test_all_known_codes_are_accepted():
    from src.api.serializers.public.contact_request import UZ_PHONE_CODES

    for code in UZ_PHONE_CODES:
        assert normalize_uz_phone(f"{code}1234567") == f"+998{code}1234567"


@pytest.mark.parametrize(
    "phone,kind",
    [
        ("+998712001122", "shahar"),  # Toshkent statsionar — do'kon raqami
        ("+998901234567", "mobil"),
    ],
)
def test_both_city_and_mobile_numbers_are_accepted(api_client, phone, kind):
    """Do'konda ko'pincha shahar raqami bo'ladi — ikkalasi ham qabul qilinadi."""
    response = _post(api_client, {"phone": phone, "region": "toshkent_shahri"})
    assert response.status_code == 201, f"{kind} raqam rad etildi: {response.json()}"
    assert models.SupportRequest.objects.get().phone == phone


def test_unknown_code_is_still_rejected():
    """Kodlar ro'yxati kengaydi, lekin ochiq emas."""
    assert normalize_uz_phone("+998012345678") is None
    assert normalize_uz_phone("+998641234567") is None


# ----------------------------------------------------------------- region


def test_invalid_region_returns_400(api_client):
    response = _post(api_client, {"phone": "+998901234567", "region": "moskva"})
    assert response.status_code == 400
    assert "region" in response.json()["error"]
    assert models.SupportRequest.objects.count() == 0


@pytest.mark.parametrize("missing", ["phone", "region"])
def test_missing_field_returns_400(api_client, missing):
    payload = {"phone": "+998901234567", "region": "andijon"}
    payload.pop(missing)
    response = _post(api_client, payload)
    assert response.status_code == 400
    assert missing in response.json()["error"]
    assert models.SupportRequest.objects.count() == 0


def test_extra_field_is_rejected(api_client):
    response = _post(
        api_client,
        {"phone": "+998901234567", "region": "andijon", "user": 1, "message": "x"},
    )
    assert response.status_code == 400
    assert models.SupportRequest.objects.count() == 0


def test_region_list_endpoint_is_public(api_client):
    response = api_client.get(reverse("api_region_list"))
    assert response.status_code == 200
    regions = response.json()["data"]["regions"]
    assert len(regions) == 14
    assert {"value": "toshkent_shahri", "label": "Toshkent shahri"} in regions


# --------------------------------------------------------------- throttling


def test_rate_limit_returns_clean_json_429(api_client):
    for i in range(3):
        assert _post(api_client).status_code == 201, f"{i + 1}-so'rov bloklandi"

    response = _post(api_client)
    assert response.status_code == 429
    assert response["Content-Type"].startswith("application/json")
    body = response.json()
    assert body["success"] is False
    assert body["data"] == {}
    assert isinstance(body["error"], str)
    assert models.SupportRequest.objects.count() == 3


def test_rate_limit_is_per_ip(api_client):
    for _ in range(3):
        _post(api_client, ip="10.0.0.1")
    assert _post(api_client, ip="10.0.0.1").status_code == 429
    assert _post(api_client, ip="10.0.0.2").status_code == 201


def test_daily_cap_applies_above_hourly(api_client, monkeypatch):
    """Soatlik chegara ko'tarilsa, kunlik 10 ta chegara ushlab qoladi."""
    _set_rate(monkeypatch, "public_contact_hour", "100/hour")
    for i in range(10):
        assert _post(api_client).status_code == 201, f"{i + 1}-so'rov bloklandi"
    assert _post(api_client).status_code == 429


# --------------------------------------------------- xatolar sizib chiqmasin


def test_internal_error_is_not_leaked(api_client, monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("DB parol: super-secret-123")

    monkeypatch.setattr(
        "src.api.views.public.contact_request.create_public_contact_request", boom
    )
    response = _post(api_client)
    assert response.status_code == 500
    payload = response.content.decode()
    assert "super-secret-123" not in payload
    assert "RuntimeError" not in payload
    assert response.json()["error"] == "Ichki server xatosi."


@override_settings(
    TELEGRAM_NOTIFICATIONS_ENABLED=True,
    TELEGRAM_SUPPORT_BOT_TOKEN="test-token",
    TELEGRAM_SUPPORT_CHAT_ID="-100123",
)
def test_telegram_network_error_does_not_break_the_request(api_client, monkeypatch):
    """Telegram yiqilsa ham 201 qaytadi va yozuv saqlanib qoladi."""
    calls = []

    def _raise(*args, **kwargs):
        calls.append(args)
        raise ConnectionError("no network")

    monkeypatch.setitem(sys.modules, "requests", _fake_requests_module(_raise))

    response = _post(api_client)
    assert response.status_code == 201
    assert len(calls) == 1, "Telegram chaqiruvi urinilishi kerak edi"
    assert models.SupportRequest.objects.count() == 1


@override_settings(
    TELEGRAM_NOTIFICATIONS_ENABLED=False,
    TELEGRAM_SUPPORT_BOT_TOKEN="test-token",
    TELEGRAM_SUPPORT_CHAT_ID="-100123",
)
def test_telegram_disabled_skips_silently(api_client):
    """O'chirilgan bo'lsa — tarmoqqa chiqmaydi (no_network fixture isbotlaydi)."""
    assert _post(api_client).status_code == 201
    assert models.SupportRequest.objects.count() == 1


# ------------------------------------------------------------- CRM ko'rinishi


def test_appears_in_crm_support_list_queryset(api_client):
    """CRM ro'yxati manba bo'yicha filtrlamaydi — yangi so'rov ko'rinadi."""
    from src.core.models import SupportRequest

    _post(api_client)
    visible = SupportRequest.objects.filter(is_deleted=False)
    assert visible.count() == 1
    assert SupportRequest.Source.PUBLIC_APP in dict(SupportRequest.Source.choices)

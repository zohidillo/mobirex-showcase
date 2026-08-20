import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from src.core import models


pytestmark = pytest.mark.django_db


def _make_request(user, **overrides):
    now = timezone.now()
    defaults = {
        "user": user,
        "request_type": models.SupportRequest.RequestType.CONTACT,
        "source": models.SupportRequest.Source.MOBILE_APP,
        "phone": "+998901234567",
        "full_name": "Test User",
        "message": "Yordam kerak",
        "status": models.SupportRequest.Status.NEW,
        "last_message_at": now,
        "last_user_message_at": now,
        "user_read_at": now if user else None,
    }
    defaults.update(overrides)
    req = models.SupportRequest.objects.create(**defaults)
    models.SupportRequestMessage.objects.create(
        request=req,
        sender=user,
        sender_type=models.SupportRequestMessage.SenderType.USER if user else models.SupportRequestMessage.SenderType.EXTERNAL,
        message=req.message,
    )
    return req


@pytest.fixture
def admin_client(users):
    client = Client()
    client.force_login(users["admin"])
    return client


@pytest.fixture
def owner_client(users):
    client = Client()
    client.force_login(users["owner"])
    return client


def test_admin_list_requires_superuser(owner_client, users):
    _make_request(users["owner"])
    resp = owner_client.get(reverse("admin_support_list"))
    # AdminRequiredMixin redirects non-superusers
    assert resp.status_code == 302


def test_admin_list_works_for_superuser(admin_client, users):
    req = _make_request(users["owner"])
    resp = admin_client.get(reverse("admin_support_list"))
    assert resp.status_code == 200
    assert f"#{req.id}".encode() in resp.content


def test_admin_list_filter_by_source(admin_client, users):
    mobile_req = _make_request(None, source=models.SupportRequest.Source.MOBILE_APP, full_name="Mobile User")
    landing_req = _make_request(None, source=models.SupportRequest.Source.LANDING_SITE, full_name="Landing User")

    resp = admin_client.get(reverse("admin_support_list") + "?source=LANDING_SITE")

    assert resp.status_code == 200
    assert b"Landing User" in resp.content
    assert b"Mobile User" not in resp.content


def test_admin_list_filter_by_status(admin_client, users):
    new_req = _make_request(None, full_name="New One", status=models.SupportRequest.Status.NEW)
    resolved_req = _make_request(None, full_name="Resolved One", status=models.SupportRequest.Status.RESOLVED)

    resp = admin_client.get(reverse("admin_support_list") + "?status=NEW")

    assert resp.status_code == 200
    assert b"New One" in resp.content
    assert b"Resolved One" not in resp.content


def test_admin_list_search_by_phone(admin_client, users):
    match_req = _make_request(None, phone="+998901111111", full_name="Phone Match")
    other_req = _make_request(None, phone="+998902222222", full_name="Phone Other")

    resp = admin_client.get(reverse("admin_support_list") + "?q=901111111")

    assert resp.status_code == 200
    assert b"Phone Match" in resp.content
    assert b"Phone Other" not in resp.content


def test_admin_detail_marks_admin_read(admin_client, users):
    req = _make_request(users["owner"])
    assert req.admin_read_at is None

    resp = admin_client.get(reverse("admin_support_detail", args=[req.pk]))

    assert resp.status_code == 200
    req.refresh_from_db()
    assert req.admin_read_at is not None


def test_admin_reply_creates_message(admin_client, users):
    req = _make_request(users["owner"])

    resp = admin_client.post(
        reverse("admin_support_reply", args=[req.pk]),
        {"message": "Salom, javob bo'lyapti"},
    )

    assert resp.status_code == 302
    req.refresh_from_db()
    admin_messages = req.messages.filter(
        sender_type=models.SupportRequestMessage.SenderType.ADMIN,
    )
    assert admin_messages.count() == 1
    assert admin_messages.first().message == "Salom, javob bo'lyapti"
    assert req.status == models.SupportRequest.Status.IN_PROGRESS


def test_admin_reply_blocked_for_telegram_source(admin_client, users):
    req = _make_request(users["owner"], source=models.SupportRequest.Source.TELEGRAM_BOT)

    resp = admin_client.post(
        reverse("admin_support_reply", args=[req.pk]),
        {"message": "Should not be sent"},
        follow=False,
    )

    assert resp.status_code == 302
    req.refresh_from_db()
    admin_messages = req.messages.filter(
        sender_type=models.SupportRequestMessage.SenderType.ADMIN,
    )
    assert admin_messages.count() == 0


def test_admin_close_updates_request(admin_client, users):
    req = _make_request(users["owner"])

    resp = admin_client.post(
        reverse("admin_support_close", args=[req.pk]),
        {
            "new_status": "RESOLVED",
            "close_reason": "SOLVED",
            "close_reason_note": "Hal qildim",
        },
    )

    assert resp.status_code == 302
    req.refresh_from_db()
    assert req.status == models.SupportRequest.Status.RESOLVED
    assert req.closed_at is not None
    assert req.closed_by == users["admin"]
    assert req.close_reason == models.SupportRequest.CloseReason.SOLVED


def test_admin_close_creates_system_message(admin_client, users):
    req = _make_request(users["owner"])

    admin_client.post(
        reverse("admin_support_close", args=[req.pk]),
        {
            "new_status": "RESOLVED",
            "close_reason": "DUPLICATE",
            "close_reason_note": "",
        },
    )

    system_messages = req.messages.filter(
        sender_type=models.SupportRequestMessage.SenderType.SYSTEM,
    )
    assert system_messages.count() == 1


def test_admin_close_blocked_when_already_closed(admin_client, users):
    req = _make_request(users["owner"])
    # First close
    admin_client.post(
        reverse("admin_support_close", args=[req.pk]),
        {"new_status": "RESOLVED", "close_reason": "SOLVED", "close_reason_note": ""},
    )
    req.refresh_from_db()
    first_closed_at = req.closed_at

    # Second close attempt
    resp = admin_client.post(
        reverse("admin_support_close", args=[req.pk]),
        {"new_status": "REJECTED", "close_reason": "OTHER", "close_reason_note": ""},
    )

    assert resp.status_code == 302
    req.refresh_from_db()
    # Still RESOLVED and original closed_at preserved
    assert req.status == models.SupportRequest.Status.RESOLVED
    assert req.closed_at == first_closed_at

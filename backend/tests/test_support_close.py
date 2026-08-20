import pytest
from django.utils import timezone

from src.core import models
from src.services.support import close_request


pytestmark = pytest.mark.django_db


def _make_request(user, **overrides):
    now = timezone.now()
    defaults = {
        "user": user,
        "request_type": models.SupportRequest.RequestType.CONTACT,
        "source": models.SupportRequest.Source.MOBILE_APP,
        "phone": "+998901234567",
        "message": "Yordam kerak",
        "status": models.SupportRequest.Status.NEW,
        "last_message_at": now,
        "last_user_message_at": now,
        "user_read_at": now if user else None,
    }
    defaults.update(overrides)
    return models.SupportRequest.objects.create(**defaults)


def test_close_request_resolved(users):
    req = _make_request(users["owner"])
    initial_admin_read = req.admin_read_at

    result = close_request(
        request_obj=req,
        closed_by=users["admin"],
        close_reason=models.SupportRequest.CloseReason.SOLVED,
        close_reason_note="Hal qildim",
        new_status=models.SupportRequest.Status.RESOLVED,
    )

    result.refresh_from_db()
    assert result.status == models.SupportRequest.Status.RESOLVED
    assert result.closed_at is not None
    assert result.closed_by == users["admin"]
    assert result.close_reason == models.SupportRequest.CloseReason.SOLVED
    assert result.close_reason_note == "Hal qildim"
    # admin_read_at unchanged
    assert result.admin_read_at == initial_admin_read


def test_close_request_rejected(users):
    req = _make_request(users["owner"])

    close_request(
        request_obj=req,
        closed_by=users["admin"],
        close_reason=models.SupportRequest.CloseReason.NOT_RELEVANT,
        new_status=models.SupportRequest.Status.REJECTED,
    )

    req.refresh_from_db()
    assert req.status == models.SupportRequest.Status.REJECTED
    assert req.close_reason == models.SupportRequest.CloseReason.NOT_RELEVANT
    assert req.close_reason_note is None


def test_close_request_invalid_status(users):
    req = _make_request(users["owner"])

    with pytest.raises(ValueError):
        close_request(
            request_obj=req,
            closed_by=users["admin"],
            close_reason=models.SupportRequest.CloseReason.SOLVED,
            new_status=models.SupportRequest.Status.NEW,
        )

    req.refresh_from_db()
    assert req.closed_at is None
    assert req.status == models.SupportRequest.Status.NEW


def test_close_request_invalid_reason(users):
    req = _make_request(users["owner"])

    with pytest.raises(ValueError):
        close_request(
            request_obj=req,
            closed_by=users["admin"],
            close_reason="NONEXISTENT_REASON",
        )

    req.refresh_from_db()
    assert req.closed_at is None


def test_close_request_creates_system_message(users):
    req = _make_request(users["owner"])

    close_request(
        request_obj=req,
        closed_by=users["admin"],
        close_reason=models.SupportRequest.CloseReason.DUPLICATE,
        close_reason_note="Allaqachon mavjud",
    )

    system_messages = req.messages.filter(
        sender_type=models.SupportRequestMessage.SenderType.SYSTEM,
    )
    assert system_messages.count() == 1
    msg = system_messages.first()
    assert "Allaqachon mavjud" in msg.message
    assert msg.metadata.get("action") == "close"
    assert msg.metadata.get("reason") == models.SupportRequest.CloseReason.DUPLICATE


def test_close_request_save_only_relevant_fields(users):
    req = _make_request(users["owner"])
    # External tampering: set full_name unsaved (should not be persisted by close_request)
    req.full_name = "TAMPERED"

    close_request(
        request_obj=req,
        closed_by=users["admin"],
        close_reason=models.SupportRequest.CloseReason.SOLVED,
    )

    fresh = models.SupportRequest.objects.get(pk=req.pk)
    # full_name was NOT in update_fields, so DB still has original value
    assert fresh.full_name != "TAMPERED"
    # close fields ARE persisted
    assert fresh.closed_at is not None


def test_close_request_blocks_double_close(users):
    req = _make_request(users["owner"])
    close_request(
        request_obj=req,
        closed_by=users["admin"],
        close_reason=models.SupportRequest.CloseReason.SOLVED,
    )

    with pytest.raises(ValueError):
        close_request(
            request_obj=req,
            closed_by=users["admin"],
            close_reason=models.SupportRequest.CloseReason.SOLVED,
        )

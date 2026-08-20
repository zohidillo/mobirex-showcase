import pytest
from django.contrib import admin
from django.test import override_settings
from django.urls import resolve, reverse
from django.utils import timezone

from src.core import models
from src.core.admin import SupportRequestAdmin
from src.api.views.support import SupportRequestDetailAPIView
from src.services.support import create_admin_reply


pytestmark = pytest.mark.django_db

SUPPORT_X_KEY = "support-secret"


def _list_url():
    return reverse("api_support_request_list_create")


def _detail_url(support_request):
    return reverse("api_support_request_detail", args=[support_request.id])


def _messages_url(support_request):
    return reverse("api_support_request_message_create", args=[support_request.id])


def _post_create(api_client, payload, *, x_key=None):
    kwargs = {"format": "json"}
    if x_key is not None:
        kwargs["HTTP_X_KEY"] = x_key
    return api_client.post(_list_url(), payload, **kwargs)


def _create_request(user, **overrides):
    now = timezone.now()
    defaults = {
        "user": user,
        "request_type": models.SupportRequest.RequestType.CONTACT,
        "source": models.SupportRequest.Source.MOBILE_APP,
        "phone": "+998901234567",
        "message": "Savolim bor",
        "status": models.SupportRequest.Status.NEW,
        "last_message_at": now,
        "last_user_message_at": now,
        "user_read_at": now if user else None,
        "admin_read_at": None,
    }
    defaults.update(overrides)
    support_request = models.SupportRequest.objects.create(**defaults)
    models.SupportRequestMessage.objects.create(
        request=support_request,
        sender=user,
        sender_type=models.SupportRequestMessage.SenderType.USER if user else models.SupportRequestMessage.SenderType.EXTERNAL,
        message=support_request.message,
    )
    return support_request


def test_authenticated_user_creates_account_delete_request(api_client, users):
    api_client.force_authenticate(user=users["owner"])

    response = _post_create(
        api_client,
        {
            "request_type": "ACCOUNT_DELETE",
            "source": "MOBILE_APP",
            "phone": "+998901234567",
            "message": "Sabab: kerak emas",
        },
    )

    assert response.status_code == 201
    support_request = models.SupportRequest.objects.get()
    assert support_request.user == users["owner"]
    assert support_request.request_type == models.SupportRequest.RequestType.ACCOUNT_DELETE
    assert support_request.status == models.SupportRequest.Status.NEW
    assert support_request.admin_read_at is None
    assert support_request.user_read_at is not None


def test_account_delete_can_have_empty_message_and_stores_default(api_client, users):
    api_client.force_authenticate(user=users["owner"])

    response = _post_create(
        api_client,
        {
            "request_type": "ACCOUNT_DELETE",
            "source": "MOBILE_APP",
            "phone": "+998901234567",
            "message": "",
        },
    )

    assert response.status_code == 201
    support_request = models.SupportRequest.objects.get()
    assert support_request.message == "Accountni o‘chirish so‘rovi yuborildi."
    assert support_request.messages.get().message == support_request.message


def test_account_delete_saves_user_metadata_snapshot(api_client, users):
    users["owner"].first_name = "Ali"
    users["owner"].last_name = "Valiyev"
    users["owner"].phone = "+998900000000"
    users["owner"].save()
    api_client.force_authenticate(user=users["owner"])

    response = _post_create(
        api_client,
        {
            "request_type": "ACCOUNT_DELETE",
            "source": "MOBILE_APP",
            "phone": "+998901234567",
            "message": "Sabab",
        },
        x_key="ignored-when-authenticated",
    )

    assert response.status_code == 201
    snapshot = models.SupportRequest.objects.get().metadata["user_snapshot"]
    assert snapshot["user_id"] == users["owner"].id
    assert snapshot["username"] == users["owner"].username
    assert snapshot["first_name"] == "Ali"
    assert snapshot["last_name"] == "Valiyev"
    assert snapshot["phone"] == "+998900000000"
    assert "mobile_pin_hash" not in snapshot
    assert "password" not in snapshot


def test_account_delete_phone_required_unless_user_phone_exists(api_client, users):
    api_client.force_authenticate(user=users["owner"])

    missing_phone = _post_create(
        api_client,
        {
            "request_type": "ACCOUNT_DELETE",
            "source": "MOBILE_APP",
            "message": "Sabab",
        },
    )
    assert missing_phone.status_code == 400

    users["owner"].phone = "+998900000000"
    users["owner"].save()
    with_user_phone = _post_create(
        api_client,
        {
            "request_type": "ACCOUNT_DELETE",
            "source": "MOBILE_APP",
            "message": "Sabab",
        },
    )

    assert with_user_phone.status_code == 201
    assert models.SupportRequest.objects.get().phone == "+998900000000"


@override_settings(SUPPORT_REQUEST_X_KEY=SUPPORT_X_KEY)
def test_contact_created_with_valid_x_key(api_client):
    response = _post_create(
        api_client,
        {
            "request_type": "CONTACT",
            "source": "LANDING_SITE",
            "full_name": "Ali",
            "phone": "+998901234567",
            "message": "Narxi qancha?",
        },
        x_key=SUPPORT_X_KEY,
    )

    assert response.status_code == 201
    support_request = models.SupportRequest.objects.get()
    assert support_request.user is None
    assert support_request.source == models.SupportRequest.Source.LANDING_SITE
    assert support_request.messages.get().sender_type == models.SupportRequestMessage.SenderType.EXTERNAL


@override_settings(SUPPORT_REQUEST_X_KEY=SUPPORT_X_KEY)
def test_missing_and_invalid_x_key_blocked(api_client):
    payload = {"request_type": "CONTACT", "message": "Narxi qancha?"}

    assert _post_create(api_client, payload).status_code == 403
    assert _post_create(api_client, payload, x_key="wrong").status_code == 403
    assert models.SupportRequest.objects.count() == 0


def test_client_cannot_set_status(api_client, users):
    api_client.force_authenticate(user=users["owner"])

    response = _post_create(
        api_client,
        {
            "request_type": "CONTACT",
            "source": "MOBILE_APP",
            "phone": "+998901234567",
            "message": "Savolim bor",
            "status": "RESOLVED",
        },
    )

    assert response.status_code == 201
    assert models.SupportRequest.objects.get().status == models.SupportRequest.Status.NEW


def test_user_lists_only_own_requests(api_client, users):
    own = _create_request(users["owner"], message="Own request")
    other = _create_request(users["outsider"], message="Other request")
    api_client.force_authenticate(user=users["owner"])

    response = api_client.get(_list_url())

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["data"]["results"]}
    assert own.id in ids
    assert other.id not in ids


def test_detail_url_resolves_to_get_enabled_detail_view():
    match = resolve("/api/support/requests/1/")

    assert match.url_name == "api_support_request_detail"
    assert match.func.view_class is SupportRequestDetailAPIView
    assert "get" in SupportRequestDetailAPIView.http_method_names
    assert hasattr(SupportRequestDetailAPIView, "get")


def test_user_cannot_see_other_user_request_detail(api_client, users):
    other = _create_request(users["outsider"])
    api_client.force_authenticate(user=users["owner"])

    response = api_client.get(_detail_url(other))

    assert response.status_code == 404


def test_detail_returns_messages(api_client, users):
    support_request = _create_request(users["owner"])
    create_admin_reply(support_request, admin_user=users["admin"], message="Admin javobi")
    api_client.force_authenticate(user=users["owner"])

    response = api_client.get(_detail_url(support_request))

    assert response.status_code == 200
    messages = response.json()["data"]["messages"]
    assert [item["sender_type"] for item in messages] == ["USER", "ADMIN"]
    assert messages[1]["message"] == "Admin javobi"


def test_opening_detail_marks_user_read_at(api_client, users):
    support_request = _create_request(users["owner"])
    create_admin_reply(support_request, admin_user=users["admin"], message="Admin javobi")
    support_request.refresh_from_db()
    assert support_request.unread_for_user is True
    api_client.force_authenticate(user=users["owner"])

    response = api_client.get(_detail_url(support_request))

    assert response.status_code == 200
    support_request.refresh_from_db()
    assert support_request.user_read_at is not None
    assert support_request.unread_for_user is False


def test_unread_for_user_true_after_admin_reply_false_after_detail_read(api_client, users):
    support_request = _create_request(users["owner"])
    create_admin_reply(support_request, admin_user=users["admin"], message="Admin javobi")
    support_request.refresh_from_db()
    api_client.force_authenticate(user=users["owner"])

    list_response = api_client.get(_list_url())
    assert list_response.json()["data"]["results"][0]["unread_for_user"] is True

    detail_response = api_client.get(_detail_url(support_request))
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["unread_for_user"] is False


def test_creating_request_creates_first_message(api_client, users):
    api_client.force_authenticate(user=users["owner"])

    response = _post_create(
        api_client,
        {
            "request_type": "CONTACT",
            "source": "MOBILE_APP",
            "phone": "+998901234567",
            "message": "Savolim bor",
        },
    )

    assert response.status_code == 201
    message = models.SupportRequest.objects.get().messages.get()
    assert message.sender == users["owner"]
    assert message.sender_type == models.SupportRequestMessage.SenderType.USER
    assert message.message == "Savolim bor"


def test_user_can_add_follow_up_message_to_own_request(api_client, users):
    support_request = _create_request(users["owner"])
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        _messages_url(support_request),
        {"message": "Yana bir savolim bor"},
        format="json",
    )

    assert response.status_code == 201
    support_request.refresh_from_db()
    assert support_request.messages.count() == 2
    assert support_request.messages.order_by("-id").first().sender_type == "USER"
    assert support_request.status == models.SupportRequest.Status.IN_PROGRESS


def test_user_cannot_add_message_to_another_users_request(api_client, users):
    support_request = _create_request(users["outsider"])
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        _messages_url(support_request),
        {"message": "Begona ticket"},
        format="json",
    )

    assert response.status_code == 404
    assert support_request.messages.count() == 1


def test_user_reply_marks_admin_unread(api_client, users):
    support_request = _create_request(users["owner"], admin_read_at=timezone.now())
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        _messages_url(support_request),
        {"message": "Yangi xabar"},
        format="json",
    )

    assert response.status_code == 201
    support_request.refresh_from_db()
    assert support_request.admin_read_at is None
    assert support_request.unread_for_admin is True


def test_admin_reply_marks_user_unread(users):
    support_request = _create_request(users["owner"])

    create_admin_reply(support_request, admin_user=users["admin"], message="Admin javobi")

    support_request.refresh_from_db()
    assert support_request.user_read_at is None
    assert support_request.last_admin_reply_at is not None
    assert support_request.unread_for_user is True
    assert support_request.status == models.SupportRequest.Status.IN_PROGRESS


@pytest.mark.parametrize("status", [models.SupportRequest.Status.RESOLVED, models.SupportRequest.Status.REJECTED])
def test_reply_to_resolved_or_rejected_request_reopens_safely(api_client, users, status):
    support_request = _create_request(users["owner"], status=status)
    api_client.force_authenticate(user=users["owner"])

    response = api_client.post(
        _messages_url(support_request),
        {"message": "Yana savol bor"},
        format="json",
    )

    assert response.status_code == 201
    support_request.refresh_from_db()
    assert support_request.status == models.SupportRequest.Status.IN_PROGRESS


def test_admin_registration_does_not_break():
    assert models.SupportRequest in admin.site._registry
    assert isinstance(admin.site._registry[models.SupportRequest], SupportRequestAdmin)


def test_admin_service_can_create_admin_reply(users):
    support_request = _create_request(users["owner"])

    reply = create_admin_reply(support_request, admin_user=users["admin"], message="Admin javobi")

    support_request.refresh_from_db()
    assert reply.sender == users["admin"]
    assert reply.sender_type == models.SupportRequestMessage.SenderType.ADMIN
    assert support_request.unread_for_user is True


@override_settings(SUPPORT_REQUEST_X_KEY=SUPPORT_X_KEY)
def test_x_key_can_create_request_but_cannot_list(api_client):
    create_response = _post_create(
        api_client,
        {"request_type": "CONTACT", "source": "LANDING_SITE", "message": "Narxi qancha?"},
        x_key=SUPPORT_X_KEY,
    )

    list_response = api_client.get(_list_url(), HTTP_X_KEY=SUPPORT_X_KEY)

    assert create_response.status_code == 201
    assert list_response.status_code in {401, 403}

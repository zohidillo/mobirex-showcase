from django.db import transaction
from django.utils import timezone

import src.core.models as models


DEFAULT_ACCOUNT_DELETE_MESSAGE = "Accountni o‘chirish so‘rovi yuborildi."


def get_client_metadata(request):
    if request is None:
        return {}
    data = {}
    meta = getattr(request, "META", {})
    ip = meta.get("HTTP_X_FORWARDED_FOR") or meta.get("REMOTE_ADDR")
    if ip:
        data["request_ip"] = ip.split(",")[0].strip()
    user_agent = meta.get("HTTP_USER_AGENT")
    if user_agent:
        data["user_agent"] = user_agent
    return data


def get_user_snapshot(user, request=None):
    if not user or not getattr(user, "is_authenticated", False):
        return {}
    snapshot = {
        "user_id": user.id,
        "username": user.get_username(),
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    if getattr(user, "phone", None):
        snapshot["phone"] = user.phone
    if hasattr(user, "roles"):
        snapshot["roles"] = sorted(user.roles)
    if hasattr(user, "get_all_branches"):
        branches = []
        for branch in user.get_all_branches():
            if branch:
                branches.append({"id": branch.id, "name": branch.name})
        if branches:
            snapshot["branches"] = branches
    snapshot.update(get_client_metadata(request))
    return snapshot


def get_initial_sender_type(support_request):
    if support_request.user_id:
        return models.SupportRequestMessage.SenderType.USER
    if support_request.source == models.SupportRequest.Source.ADMIN:
        return models.SupportRequestMessage.SenderType.ADMIN
    return models.SupportRequestMessage.SenderType.EXTERNAL


def create_initial_message(support_request, *, at=None):
    at = at or timezone.now()
    sender_type = get_initial_sender_type(support_request)
    message = models.SupportRequestMessage.objects.create(
        request=support_request,
        sender=support_request.user,
        sender_type=sender_type,
        message=support_request.message,
        metadata=support_request.metadata or {},
    )
    if sender_type == models.SupportRequestMessage.SenderType.USER:
        support_request.last_user_message_at = at
        support_request.user_read_at = at
        support_request.admin_read_at = None
    elif sender_type == models.SupportRequestMessage.SenderType.ADMIN:
        support_request.last_admin_reply_at = at
        support_request.admin_read_at = at
        support_request.user_read_at = None
    else:
        support_request.last_user_message_at = at
        support_request.user_read_at = None
        support_request.admin_read_at = None
    support_request.last_message_at = at
    support_request.save(
        update_fields=[
            "last_user_message_at",
            "last_admin_reply_at",
            "last_message_at",
            "user_read_at",
            "admin_read_at",
            "updated_at",
        ]
    )
    return message


def create_support_request(*, validated_data, user=None, request=None):
    at = timezone.now()
    data = dict(validated_data)
    metadata = dict(data.pop("metadata", {}) or {})
    request_type = data.get("request_type")
    if request_type == models.SupportRequest.RequestType.ACCOUNT_DELETE:
        metadata["user_snapshot"] = get_user_snapshot(user, request)
        if not data.get("message"):
            data["message"] = DEFAULT_ACCOUNT_DELETE_MESSAGE
        if not data.get("phone") and user and getattr(user, "phone", None):
            data["phone"] = user.phone

    support_request = models.SupportRequest.objects.create(
        **data,
        metadata=metadata,
        user=user if user and getattr(user, "is_authenticated", False) else None,
        status=models.SupportRequest.Status.NEW,
        last_message_at=at,
        last_user_message_at=at,
        user_read_at=at if user and getattr(user, "is_authenticated", False) else None,
        admin_read_at=None,
    )
    create_initial_message(support_request, at=at)
    return support_request


def create_user_reply(support_request, *, user, message, metadata=None):
    at = timezone.now()
    reply = models.SupportRequestMessage.objects.create(
        request=support_request,
        sender=user,
        sender_type=models.SupportRequestMessage.SenderType.USER,
        message=message,
        metadata=metadata or {},
    )
    support_request.last_user_message_at = at
    support_request.last_message_at = at
    support_request.admin_read_at = None
    if support_request.status in {
        models.SupportRequest.Status.NEW,
        models.SupportRequest.Status.RESOLVED,
        models.SupportRequest.Status.REJECTED,
    }:
        support_request.status = models.SupportRequest.Status.IN_PROGRESS
    support_request.save(
        update_fields=[
            "last_user_message_at",
            "last_message_at",
            "admin_read_at",
            "status",
            "updated_at",
        ]
    )
    return reply


def create_admin_reply(support_request, *, admin_user=None, message, metadata=None):
    at = timezone.now()
    reply = models.SupportRequestMessage.objects.create(
        request=support_request,
        sender=admin_user if admin_user and getattr(admin_user, "is_authenticated", False) else None,
        sender_type=models.SupportRequestMessage.SenderType.ADMIN,
        message=message,
        metadata=metadata or {},
    )
    support_request.last_admin_reply_at = at
    support_request.last_message_at = at
    support_request.user_read_at = None
    if support_request.status == models.SupportRequest.Status.NEW:
        support_request.status = models.SupportRequest.Status.IN_PROGRESS
    support_request.save(
        update_fields=[
            "last_admin_reply_at",
            "last_message_at",
            "user_read_at",
            "status",
            "updated_at",
        ]
    )
    return reply


def mark_user_read(support_request):
    support_request.user_read_at = timezone.now()
    support_request.save(update_fields=["user_read_at", "updated_at"])
    return support_request


def mark_admin_read(support_request):
    support_request.admin_read_at = timezone.now()
    support_request.save(update_fields=["admin_read_at", "updated_at"])
    return support_request


def close_request(
    *,
    request_obj,
    closed_by,
    close_reason,
    close_reason_note="",
    new_status=None,
):
    if new_status is None:
        new_status = models.SupportRequest.Status.RESOLVED
    if new_status not in (
        models.SupportRequest.Status.RESOLVED,
        models.SupportRequest.Status.REJECTED,
    ):
        raise ValueError("new_status must be RESOLVED or REJECTED")
    if close_reason not in models.SupportRequest.CloseReason.values:
        raise ValueError("invalid close_reason")
    if request_obj.closed_at is not None:
        raise ValueError("request already closed")

    note = (close_reason_note or "").strip()
    with transaction.atomic():
        request_obj.status = new_status
        request_obj.closed_at = timezone.now()
        request_obj.closed_by = closed_by if closed_by and getattr(closed_by, "is_authenticated", False) else None
        request_obj.close_reason = close_reason
        request_obj.close_reason_note = note or None
        request_obj.save(update_fields=[
            "status",
            "closed_at",
            "closed_by",
            "close_reason",
            "close_reason_note",
            "updated_at",
        ])

        reason_label = request_obj.get_close_reason_display()
        system_text = f"Yopildi: {reason_label}."
        if note:
            system_text = f"{system_text} {note}"
        models.SupportRequestMessage.objects.create(
            request=request_obj,
            sender=request_obj.closed_by,
            sender_type=models.SupportRequestMessage.SenderType.SYSTEM,
            message=system_text,
            metadata={"action": "close", "reason": close_reason, "status": new_status},
        )
    return request_obj

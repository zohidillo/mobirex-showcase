from django.db.models import F, Q

from src.shared.navigation import get_back_url, should_show_back_button


def _compute_unread_support_count(user):
    if not user or not getattr(user, "is_superuser", False):
        return 0
    from src.core.models import SupportRequest

    return (
        SupportRequest.objects.filter(
            is_deleted=False,
            status__in=[SupportRequest.Status.NEW, SupportRequest.Status.IN_PROGRESS],
            last_user_message_at__isnull=False,
        )
        .filter(Q(admin_read_at__isnull=True) | Q(admin_read_at__lt=F("last_user_message_at")))
        .count()
    )


def role_flags(request):
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {
            "is_owner": False,
            "is_phone_seller": False,
            "is_accessory_seller": False,
            "account_warning_message": "",
            "billing_status": "",
            "show_back_button": False,
            "back_url": "",
            "unread_support_count": 0,
        }

    show_back_button = should_show_back_button(request)
    return {
        "is_owner": user.has_role("OWNER"),
        "is_phone_seller": user.has_role("PHONE_SELLER"),
        "is_accessory_seller": user.has_role("ACCESSORY_SELLER"),
        "account_warning_message": getattr(request, "account_warning_message", ""),
        "billing_status": getattr(user, "account_status", ""),
        "show_back_button": show_back_button,
        "back_url": get_back_url(request) if show_back_button else "",
        "unread_support_count": _compute_unread_support_count(user),
    }

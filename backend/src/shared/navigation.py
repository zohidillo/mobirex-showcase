from django.urls import NoReverseMatch, reverse

from .permissions import get_owner_branches


SOLD_PRODUCT_BACK_VIEW_NAMES = {
    "phone_sold_list": "phone_unsold_list",
    "accessory_sold_list": "accessory_unsold_list",
}

DEBT_CHILD_VIEW_NAMES = {
    "debt_create",
    "debt_delete",
    "debt_paid_list",
    "debt_payment_create",
    "debt_payment_delete",
    "debt_payment_list",
}

HIDDEN_BACK_BUTTON_VIEW_NAMES = {
    "login",
    "logout",
    "dashboard",
    "debt_payment_debt_options",
}


def _safe_reverse(name, *, fallback="dashboard"):
    try:
        return reverse(name)
    except NoReverseMatch:
        if fallback and fallback != name:
            return _safe_reverse(fallback, fallback=None)
        return "/"


def _get_view_name(request, context=None):
    if context and context.get("view_name"):
        return context["view_name"]

    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match:
        return resolver_match.url_name or ""
    return ""


def _detect_module(request, context=None):
    if context and context.get("module"):
        return context["module"]

    view_name = _get_view_name(request, context=context)
    path = getattr(request, "path", "") or ""

    if view_name.startswith("debt_") or path.startswith("/debt/"):
        return "debt"
    if view_name.startswith("phone_") or path.startswith("/phone/"):
        return "phone"
    if view_name.startswith("accessory_") or path.startswith("/accessory/"):
        return "accessory"
    return ""


def _has_role(user, role):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and hasattr(user, "has_role")
        and user.has_role(role)
    )


def _is_owner(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and get_owner_branches(user)
    )


def _is_hidden_role(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (getattr(user, "is_superuser", False) or getattr(user, "is_cashier", False))
    )


def get_main_page_url(user):
    # Role priority is intentional: phone seller > accessory seller > owner.
    if _has_role(user, "PHONE_SELLER"):
        return _safe_reverse("phone_unsold_list")
    if _has_role(user, "ACCESSORY_SELLER"):
        return _safe_reverse("accessory_unsold_list", fallback="accessory_unsold_list_legacy")
    if _is_owner(user):
        return _safe_reverse("owner-branches")
    return _safe_reverse("dashboard")


def get_back_url(request, context=None):
    if context:
        explicit_back_url = context.get("back_url")
        if explicit_back_url:
            return explicit_back_url

        explicit_view_name = context.get("back_view_name")
        if explicit_view_name:
            return _safe_reverse(explicit_view_name)

    user = getattr(request, "user", None)
    main_page_url = get_main_page_url(user)

    view_name = _get_view_name(request, context=context)
    if view_name in SOLD_PRODUCT_BACK_VIEW_NAMES:
        target_view_name = SOLD_PRODUCT_BACK_VIEW_NAMES[view_name]
        return _safe_reverse(
            target_view_name,
            fallback="accessory_unsold_list_legacy"
            if target_view_name == "accessory_unsold_list"
            else "dashboard",
        )

    if view_name == "debt_list":
        return main_page_url

    module = _detect_module(request, context=context)
    if view_name in DEBT_CHILD_VIEW_NAMES or (
        module == "debt" and view_name and view_name != "debt_payment_debt_options"
    ):
        return _safe_reverse("debt_list")

    return main_page_url


def should_show_back_button(request, context=None):
    if context and "show_back_button" in context:
        return bool(context["show_back_button"])

    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if _is_hidden_role(user):
        return False

    view_name = _get_view_name(request, context=context)
    if not view_name:
        return False

    return view_name not in HIDDEN_BACK_BUTTON_VIEW_NAMES

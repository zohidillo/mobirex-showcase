"""Custom API exceptions shared across views."""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException


class AccountBlocked(APIException):
    """Raised when a billing-blocked user hits a protected API endpoint.

    Rendered as HTTP 402 with a structured ``account_blocked`` error so the
    mobile app can route the user to the blocked screen instead of showing a
    raw error. Login and ``/api/me/`` are intentionally not affected.
    """

    status_code = 402
    default_detail = _("Siz to‘lov qilishingiz kerak. Hozirgi holatingiz bloklangan.")
    default_code = "account_blocked"

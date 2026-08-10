from django.http import JsonResponse

from src.shared.json_utils import json_safe


def success_response(data=None, *, status=200):
    """Return a standard success JSON response."""
    payload = {
        "success": True,
        "data": json_safe({} if data is None else data),
        "error": None,
    }
    return JsonResponse(payload, status=status)


def error_response(message, *, status=400):
    """Return a standard error JSON response."""
    payload = {
        "success": False,
        "data": {},
        "error": str(message),
    }
    return JsonResponse(payload, status=status)


def account_blocked_response(message, *, account_status="blocked"):
    """Return the structured billing-blocked response (HTTP 402).

    Unlike ``error_response``, ``error`` is an object so the mobile app can key
    on ``error.code == "account_blocked"`` (in addition to the 402 status) and
    route to the blocked screen. Login and ``/api/me/`` do not use this.
    """
    payload = {
        "success": False,
        "data": None,
        "error": {
            "code": "account_blocked",
            "message": str(message),
            "account_status": account_status,
        },
    }
    return JsonResponse(payload, status=402)

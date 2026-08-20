"""Shared DRF permissions."""

from rest_framework.permissions import BasePermission

from src.services.billing import AccountAccessService

from src.api.exceptions import AccountBlocked


class IsAccountActive(BasePermission):
    """Deny billing-blocked users with a structured 402 response.

    Applied automatically to every ``BaseAPIView`` endpoint. Anonymous users
    are allowed through so ``IsAuthenticated`` can produce the usual 401.
    VIP/demo users are always allowed because ``evaluate_user`` reports them as
    allowed. The check is read-only (``persist=False``) — it never mutates the
    account, it only reflects the billing state the daily-charge job maintains.
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return True

        decision = AccountAccessService.evaluate_user(user, persist=False)
        if not decision.is_allowed:
            raise AccountBlocked(decision.blocked_message or AccountBlocked.default_detail)
        return True

"""Login serializer."""

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from src.services.billing import AccountAccessService


class AuthLoginSerializer(TokenObtainPairSerializer):
    """Authenticate with SimpleJWT and keep token payload minimal."""

    default_error_messages = {
        "no_active_account": _("Login yoki parol noto‘g‘ri."),
    }

    def validate(self, attrs):
        """Validate credentials and enforce existing account access rules."""
        data = super().validate(attrs)

        if getattr(self.user, "is_deleted", False):
            raise AuthenticationFailed(_("Hisob o‘chirilgan."))

        decision = AccountAccessService.evaluate_user(self.user, persist=True)
        if not decision.is_allowed:
            # Structured detail so the mobile login page can tell a blocked
            # account apart from wrong credentials (both are HTTP 401).
            raise AuthenticationFailed(
                {
                    "detail": decision.blocked_message,
                    "code": "account_blocked",
                    "account_status": decision.status,
                }
            )

        return data

"""Self-service account deletion view (Apple App Store requirement)."""

import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema

from src.api.base import BaseAPIView
from src.api.schema import build_message_data_schema, build_success_response_schema
from src.api.serializers.account import AccountDeleteSerializer
from src.services.user import UserDeleteService
from src.shared.demo import block_demo_user


logger = logging.getLogger(__name__)


ACCOUNT_DELETE_RESPONSE_SCHEMA = build_success_response_schema(
    "AccountDeleteResponse",
    build_message_data_schema("AccountDeleteResponseData"),
)


class AccountDeleteAPIView(BaseAPIView):
    """Let the authenticated user soft-delete their own account."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Account"],
        request=AccountDeleteSerializer,
        responses={200: ACCOUNT_DELETE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Soft-delete the current account and blacklist the refresh token."""
        block_demo_user(request.user)

        serializer = AccountDeleteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        UserDeleteService.soft_delete_account(request.user)

        refresh_token = serializer.validated_data.get("refresh")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                # An invalid/expired refresh token must not block the deletion.
                logger.warning("Account delete: could not blacklist refresh token.")

        return self.success({"message": "Hisobingiz o‘chirildi."}, status=200)

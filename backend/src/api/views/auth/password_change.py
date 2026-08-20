"""Password change view."""

from django.contrib.auth import update_session_auth_hash
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from src.api.base import BaseAPIView
from src.api.schema import build_message_data_schema, build_success_response_schema
from src.api.serializers.auth import PasswordChangeSerializer
from src.shared.demo import block_demo_user


PASSWORD_CHANGE_RESPONSE_SCHEMA = build_success_response_schema(
    "PasswordChangeResponse",
    build_message_data_schema("PasswordChangeResponseData"),
)


class PasswordChangeAPIView(BaseAPIView):
    """Change the authenticated user's password."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        request=PasswordChangeSerializer,
        responses={200: PASSWORD_CHANGE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Validate and update the current user's password."""
        block_demo_user(request.user)
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        update_session_auth_hash(request._request, user)
        return self.success({"message": "Parol muvaffaqiyatli yangilandi."}, status=200)

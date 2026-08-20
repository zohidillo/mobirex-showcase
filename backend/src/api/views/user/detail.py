"""User detail view."""

from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.user import UserDetailSerializer
from src.api.views.user.list import UserAdminAccessMixin


USER_DETAIL_RESPONSE_SCHEMA = build_success_response_schema(
    "UserDetailResponse",
    UserDetailSerializer,
)


class UserDetailAPIView(UserAdminAccessMixin, BaseAPIView):
    """Retrieve a user. Superadmin only."""

    def get_object(self):
        """Return the requested active user."""
        self.require_admin(self.request.user)
        return get_object_or_404(
            models.User.objects.prefetch_related("branch_roles__branch", "owned_branches"),
            pk=self.kwargs["pk"],
            is_deleted=False,
        )

    @extend_schema(
        tags=["User"],
        operation_id="users_detail",
        responses={200: USER_DETAIL_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return the requested user."""
        serializer = UserDetailSerializer(self.get_object(), context={"request": request})
        return self.success(serializer.data)

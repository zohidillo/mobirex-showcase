"""Branch-user list view."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import PAGINATION_PARAMETERS, build_paginated_response_schema
from src.api.serializers.branch_user import BranchUserListSerializer
from src.shared.permissions import is_superuser


BRANCH_USER_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "BranchUserListResponse",
    BranchUserListSerializer,
)


class BranchUserAdminAccessMixin:
    """Limit branch-user APIs to superadmins."""

    permission_classes = [IsAuthenticated]

    def require_admin(self, user):
        """Ensure the user is a superadmin."""
        if not is_superuser(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))


class BranchUserListAPIView(BranchUserAdminAccessMixin, BaseAPIView):
    """List branch role assignments. Superadmin only."""

    def get_queryset(self):
        """Return the filtered branch-role queryset."""
        self.require_admin(self.request.user)
        queryset = (
            models.BranchUser.objects.filter(is_deleted=False)
            .select_related("user", "branch")
            .order_by("-added_at")
        )

        user_id = self.request.query_params.get("user")
        branch_id = self.request.query_params.get("branch")
        role = self.request.query_params.get("role")

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        if role:
            queryset = queryset.filter(role=role)
        return queryset

    @extend_schema(
        tags=["Branch User"],
        parameters=[
            *PAGINATION_PARAMETERS,
            OpenApiParameter(name="user", type=int, required=False),
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="role", type=str, required=False),
        ],
        responses={200: BRANCH_USER_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated branch-role data."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = BranchUserListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

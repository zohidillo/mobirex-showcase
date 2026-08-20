"""User list view."""

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import PAGINATION_PARAMETERS, build_paginated_response_schema
from src.api.serializers.user import UserListSerializer
from src.shared.permissions import is_superuser


USER_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "UserListResponse",
    UserListSerializer,
)


def _parse_bool_param(value):
    """Parse a query-string boolean value."""
    if value is None or value == "":
        return None
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


class UserAdminAccessMixin:
    """Limit admin user APIs to superadmins."""

    permission_classes = [IsAuthenticated]

    def require_admin(self, user):
        """Ensure the user is a superadmin."""
        if not is_superuser(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))


class UserListAPIView(UserAdminAccessMixin, BaseAPIView):
    """List users. Superadmin only."""

    def get_queryset(self):
        """Return the filtered admin user queryset."""
        self.require_admin(self.request.user)
        queryset = models.User.objects.filter(is_deleted=False).order_by("username")

        is_active = _parse_bool_param(self.request.query_params.get("active"))
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        role = (self.request.query_params.get("role") or "").strip().upper()
        if role == "CASHIER":
            queryset = queryset.filter(is_cashier=True)
        elif role == "SUPERADMIN":
            queryset = queryset.filter(is_superuser=True)
        elif role in {
            models.BranchUser.ROLE_OWNER,
            models.BranchUser.ROLE_PHONE_SELLER,
            models.BranchUser.ROLE_ACCESSORY_SELLER,
        }:
            queryset = queryset.filter(branch_roles__role=role, branch_roles__is_deleted=False)

        branch = self.request.query_params.get("branch")
        if branch:
            queryset = queryset.filter(
                Q(branch_roles__branch_id=branch, branch_roles__is_deleted=False)
                | Q(owned_branches__id=branch, owned_branches__is_deleted=False)
            )

        return queryset.distinct()

    @extend_schema(
        tags=["User"],
        operation_id="users_list",
        parameters=[
            *PAGINATION_PARAMETERS,
            OpenApiParameter(name="active", type=bool, required=False),
            OpenApiParameter(name="role", type=str, required=False),
            OpenApiParameter(name="branch", type=int, required=False),
        ],
        responses={200: USER_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated user data."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = UserListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

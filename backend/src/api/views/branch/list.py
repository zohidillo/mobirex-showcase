"""Branch list view."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import PAGINATION_PARAMETERS, build_paginated_response_schema
from src.api.serializers.branch import BranchListSerializer
from src.shared.permissions import is_superuser


BRANCH_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "BranchListResponse",
    BranchListSerializer,
)


class BranchAdminAccessMixin:
    """Limit branch admin APIs to superadmins."""

    permission_classes = [IsAuthenticated]

    def require_admin(self, user):
        """Ensure the user is a superadmin."""
        if not is_superuser(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))


class BranchListAPIView(BranchAdminAccessMixin, BaseAPIView):
    """List branches. Superadmin only."""

    def get_queryset(self):
        """Return the admin branch queryset."""
        self.require_admin(self.request.user)
        return (
            models.Branch.objects.filter(is_deleted=False)
            .select_related("owner")
            .order_by("-added_at")
        )

    @extend_schema(
        tags=["Branch"],
        parameters=PAGINATION_PARAMETERS,
        responses={200: BRANCH_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated branch data."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = BranchListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

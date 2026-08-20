"""Branch-user update view."""

from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.branch_user import BranchUserListSerializer, BranchUserUpdateSerializer
from src.api.views.branch_user.list import BranchUserAdminAccessMixin


BRANCH_USER_UPDATE_RESPONSE_SCHEMA = build_success_response_schema(
    "BranchUserUpdateResponse",
    BranchUserListSerializer,
)


class BranchUserUpdateAPIView(BranchUserAdminAccessMixin, BaseAPIView):
    """Update branch role assignments. Superadmin only."""

    def get_object(self):
        """Return the requested active branch role."""
        self.require_admin(self.request.user)
        return get_object_or_404(
            models.BranchUser.objects.select_related("user", "branch"),
            pk=self.kwargs["pk"],
            is_deleted=False,
        )

    @extend_schema(
        tags=["Branch User"],
        request=BranchUserUpdateSerializer,
        responses={200: BRANCH_USER_UPDATE_RESPONSE_SCHEMA},
    )
    def patch(self, request, *args, **kwargs):
        """Update a branch role assignment."""
        branch_user = self.get_object()
        serializer = BranchUserUpdateSerializer(
            branch_user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        branch_user = serializer.save()
        return self.success(BranchUserListSerializer(branch_user, context={"request": request}).data)

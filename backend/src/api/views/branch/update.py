"""Branch update view."""

from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.branch import BranchListSerializer, BranchUpdateSerializer
from src.api.views.branch.list import BranchAdminAccessMixin
from src.services.branch import BranchUpdateService


BRANCH_UPDATE_RESPONSE_SCHEMA = build_success_response_schema(
    "BranchUpdateResponse",
    BranchListSerializer,
)


class BranchUpdateAPIView(BranchAdminAccessMixin, BaseAPIView):
    """Update branches. Superadmin only."""

    def get_object(self):
        """Return the requested branch."""
        self.require_admin(self.request.user)
        return get_object_or_404(
            models.Branch.objects.select_related("owner"),
            pk=self.kwargs["pk"],
            is_deleted=False,
        )

    @extend_schema(
        tags=["Branch"],
        request=BranchUpdateSerializer,
        responses={200: BRANCH_UPDATE_RESPONSE_SCHEMA},
    )
    def patch(self, request, *args, **kwargs):
        """Partially update a branch through the existing service."""
        branch = self.get_object()
        serializer = BranchUpdateSerializer(
            branch,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        branch = BranchUpdateService.update_branch(
            branch,
            validated_data=serializer.validated_data,
            updated_by=request.user,
        )
        return self.success(BranchListSerializer(branch, context={"request": request}).data)

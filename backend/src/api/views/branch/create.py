"""Branch create view."""

from drf_spectacular.utils import extend_schema

from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.branch import BranchCreateSerializer, BranchListSerializer
from src.api.views.branch.list import BranchAdminAccessMixin


BRANCH_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "BranchCreateResponse",
    BranchListSerializer,
)


class BranchCreateAPIView(BranchAdminAccessMixin, BaseAPIView):
    """Create branches. Superadmin only."""

    @extend_schema(
        tags=["Branch"],
        request=BranchCreateSerializer,
        responses={201: BRANCH_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Create a branch via the existing branch service."""
        self.require_admin(request.user)
        serializer = BranchCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        return self.success(
            BranchListSerializer(branch, context={"request": request}).data,
            status=201,
        )

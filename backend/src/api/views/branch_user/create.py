"""Branch-user create view."""

from drf_spectacular.utils import extend_schema

from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.branch_user import BranchUserCreateSerializer, BranchUserListSerializer
from src.api.views.branch_user.list import BranchUserAdminAccessMixin


BRANCH_USER_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "BranchUserCreateResponse",
    BranchUserListSerializer,
)


class BranchUserCreateAPIView(BranchUserAdminAccessMixin, BaseAPIView):
    """Create branch role assignments. Superadmin only."""

    @extend_schema(
        tags=["Branch User"],
        request=BranchUserCreateSerializer,
        responses={201: BRANCH_USER_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Create or revive a branch role assignment."""
        self.require_admin(request.user)
        serializer = BranchUserCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        branch_user = serializer.save()
        return self.success(
            BranchUserListSerializer(branch_user, context={"request": request}).data,
            status=201,
        )

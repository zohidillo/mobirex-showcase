"""Owner branches helper API."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from src.api.base import BaseAPIView
from src.api.serializers.me.branches import OwnerBranchSerializer
from src.shared.permissions import get_owner_branches, is_owner


class OwnerBranchListAPIView(BaseAPIView):
    """Return branches owned by the authenticated user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Me"],
        responses={200: OwnerBranchSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        if not is_owner(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))
        branches = get_owner_branches(user)
        serializer = OwnerBranchSerializer(branches, many=True)
        return self.success(serializer.data)

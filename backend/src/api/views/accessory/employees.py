from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.serializers.accessory import AccessoryEmployeeSerializer
from src.shared.permissions import get_owner_branches, is_owner


class AccessoryEmployeeListAPIView(BaseAPIView):
    """List owner employees for accessory filter dropdowns."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not is_owner(user):
            raise PermissionDenied(_("Ruxsat yo‘q."))

        owner_branches = get_owner_branches(user)
        branch_ids = [branch.id for branch in owner_branches if branch]
        if not branch_ids:
            return models.BranchUser.objects.none()

        queryset = models.BranchUser.objects.filter(
            is_deleted=False,
            branch_id__in=branch_ids,
            role__in=[
                models.BranchUser.ROLE_PHONE_SELLER,
                models.BranchUser.ROLE_ACCESSORY_SELLER,
            ],
        ).select_related("user", "branch")

        role = self.request.query_params.get("role")
        if role in {
            models.BranchUser.ROLE_PHONE_SELLER,
            models.BranchUser.ROLE_ACCESSORY_SELLER,
        }:
            queryset = queryset.filter(role=role)

        branch_id = self.request.query_params.get("branch")
        if branch_id:
            try:
                branch_id_int = int(branch_id)
            except (TypeError, ValueError):
                branch_id_int = None
            if branch_id_int in branch_ids:
                queryset = queryset.filter(branch_id=branch_id_int)

        return queryset.order_by("branch_id", "role", "user__username")

    @extend_schema(
        tags=["Accessory"],
        parameters=[
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="role", type=str, required=False),
        ],
        responses={200: AccessoryEmployeeSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = AccessoryEmployeeSerializer(queryset, many=True, context={"request": request})
        return self.success(serializer.data)

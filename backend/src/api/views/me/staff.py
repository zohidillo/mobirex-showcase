"""Owner staff helper API."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.serializers.me.staff import OwnerStaffSerializer
from src.shared.permissions import get_owner_branch_ids, is_owner

SELLER_ROLES = [
    models.BranchUser.ROLE_PHONE_SELLER,
    models.BranchUser.ROLE_ACCESSORY_SELLER,
]


class OwnerStaffListAPIView(BaseAPIView):
    """Return sellers in owner's branches. Optional ?branch=<id> filter."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Me"],
        parameters=[
            OpenApiParameter(name="branch", type=int, required=False),
        ],
        responses={200: OwnerStaffSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        if not is_owner(user):
            raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

        owner_branch_ids = get_owner_branch_ids(user)

        queryset = (
            models.BranchUser.objects.filter(
                branch_id__in=owner_branch_ids,
                role__in=SELLER_ROLES,
                is_deleted=False,
            )
            .select_related("user", "branch")
            .order_by("branch__name", "user__username")
        )

        branch_param = request.query_params.get("branch")
        if branch_param:
            try:
                branch_id_int = int(branch_param)
            except (TypeError, ValueError):
                branch_id_int = None
            if branch_id_int in owner_branch_ids:
                queryset = queryset.filter(branch_id=branch_id_int)
            else:
                queryset = queryset.none()

        serializer = OwnerStaffSerializer(queryset, many=True)
        return self.success(serializer.data)

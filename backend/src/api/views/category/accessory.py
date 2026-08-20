"""Accessory category views."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import PAGINATION_PARAMETERS, build_paginated_response_schema
from src.api.serializers.category import AccessoryCategorySerializer
from src.shared.permissions import is_superuser


ACCESSORY_CATEGORY_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "AccessoryCategoryListResponse",
    AccessoryCategorySerializer,
)


class AccessoryCategoryListAPIView(BaseAPIView):
    """List accessory categories. Superadmin only."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the accessory category queryset."""
        return (
            models.AccessoryCategory.objects.filter(is_deleted=False)
            .only("id", "name", "added_at")
            .order_by("name")
        )

    @extend_schema(
        tags=["Category"],
        parameters=PAGINATION_PARAMETERS,
        responses={200: ACCESSORY_CATEGORY_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated accessory categories."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AccessoryCategorySerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

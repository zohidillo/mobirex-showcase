"""Journal list views."""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import YEAR_MONTH_PARAMETERS, build_paginated_response_schema
from src.api.serializers.journal import JournalListSerializer
from src.shared.filters import get_filtered_queryset
from src.shared.permissions import (
    get_owner_branches,
    is_accessory_seller,
    is_owner,
    is_phone_seller,
    is_superuser,
)


JOURNAL_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "JournalListResponse",
    JournalListSerializer,
)


class JournalListAPIView(BaseAPIView):
    """List journal entries. Owner sees branch data. Seller sees own data."""

    permission_classes = [IsAuthenticated]

    def get_base_queryset(self):
        """Return the role-scoped journal queryset."""
        user = self.request.user
        queryset = models.Journal.objects.select_related("user", "branch")

        if is_superuser(user):
            return queryset

        if is_owner(user):
            branches = get_owner_branches(user)
            if not branches:
                return models.Journal.objects.none()
            return queryset.filter(branch__in=branches)

        if is_phone_seller(user):
            branch = user.get_primary_branch("PHONE_SELLER")
            if not branch:
                return models.Journal.objects.none()
            return queryset.filter(
                branch=branch,
                model_name__in=["phone", "debt", "expense", "extra_profit"],
                user=user,
            )

        if is_accessory_seller(user):
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch:
                return models.Journal.objects.none()
            return queryset.filter(
                branch=branch,
                model_name__in=["accessory", "accessorysale", "debt", "expense"],
                user=user,
            )

        raise PermissionDenied(_("Sizga bu amalni bajarish mumkin emas."))

    def get_queryset(self):
        """Build the filtered journal queryset."""
        queryset = self.get_base_queryset()

        action = self.request.query_params.get("action")
        model_name = self.request.query_params.get("model_name")

        if action:
            queryset = queryset.filter(action=action)
        if model_name:
            queryset = queryset.filter(model_name=model_name)

        if is_superuser(self.request.user):
            user_id = self.request.query_params.get("user")
            if user_id:
                queryset = queryset.filter(user_id=user_id)

        return get_filtered_queryset(
            queryset.order_by("-added_at"),
            self.request,
            field_name="added_at",
        )

    @extend_schema(
        tags=["Journal"],
        parameters=[
            *YEAR_MONTH_PARAMETERS,
            OpenApiParameter(name="action", type=str, required=False),
            OpenApiParameter(name="model_name", type=str, required=False),
            OpenApiParameter(name="user", type=int, required=False),
        ],
        responses={200: JOURNAL_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        """Return paginated journal entries."""
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = JournalListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

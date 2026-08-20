from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import OpenApiParameter, extend_schema

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import (
    PAGINATION_PARAMETERS,
    YEAR_MONTH_PARAMETERS,
    build_message_data_schema,
    build_paginated_response_schema,
    build_success_response_schema,
)
from src.api.serializers.phone import PhoneCreateSerializer, PhoneListSerializer, PhoneSellSerializer
from src.services.phone import PhoneService
from src.shared.filters import filter_by_month


PHONE_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "PhoneListResponse",
    PhoneListSerializer,
)
PHONE_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "PhoneCreateResponse",
    PhoneListSerializer,
)
PHONE_SELL_RESPONSE_SCHEMA = build_success_response_schema(
    "PhoneSellResponse",
    PhoneListSerializer,
)
PHONE_RETURN_RESPONSE_SCHEMA = build_success_response_schema(
    "PhoneReturnResponse",
    PhoneListSerializer,
)
PHONE_DELETE_RESPONSE_SCHEMA = build_success_response_schema(
    "PhoneDeleteResponse",
    build_message_data_schema("PhoneDeleteData"),
)


class PhoneAccessMixin:
    """Share phone access helpers between endpoints."""

    permission_classes = [IsAuthenticated]

    def require_access(self, user):
        """Ensure the user can access phone endpoints."""
        if not (user.has_role("OWNER") or user.has_role("PHONE_SELLER")):
            raise PermissionDenied(_("Ruxsat yo‘q."))

    def get_branch_queryset(self, queryset):
        """Apply branch isolation rules to the queryset."""
        user = self.request.user
        if user.has_role("OWNER"):
            branches = user.get_all_branches("OWNER")
            branch_ids = [branch.id for branch in branches if branch]
            if not branch_ids:
                return queryset.none()
            queryset = queryset.filter(branch_id__in=branch_ids)
            branch_id = self.request.query_params.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)
            return queryset

        if user.has_role("PHONE_SELLER"):
            branch = user.get_primary_branch("PHONE_SELLER")
            if not branch:
                return queryset.none()
            return queryset.filter(branch=branch)

        return queryset.none()

    def apply_phone_filters(self, queryset):
        """Apply search filters shared between sold and unsold lists."""
        q = self.request.query_params.get("q")
        imei = self.request.query_params.get("imei")
        name = self.request.query_params.get("name")
        storage = self.request.query_params.get("storage")
        category = self.request.query_params.get("category")

        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(imei__icontains=q))
        if imei:
            queryset = queryset.filter(imei__icontains=imei)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if storage:
            queryset = queryset.filter(storage=storage)
        if category:
            queryset = queryset.filter(category_id=category)

        return queryset


class PhoneCreateAPIView(PhoneAccessMixin, BaseAPIView):
    """Create a phone with the same branch rules as web."""

    @extend_schema(
        tags=["Phone"],
        request=PhoneCreateSerializer,
        responses={201: PHONE_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        self.require_access(request.user)
        data = request.data.copy()
        if not request.user.has_role("OWNER"):
            data.pop("branch", None)

        serializer = PhoneCreateSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        if request.user.has_role("OWNER"):
            owner_branch_ids = {
                branch.id for branch in request.user.get_all_branches("OWNER") if branch
            }
            branch = serializer.validated_data.get("branch")
            if not owner_branch_ids or not branch or branch.id not in owner_branch_ids:
                raise PermissionDenied(_("Sizda bu filialga ruxsat yo‘q."))

        phone = serializer.save()
        return self.success(
            PhoneListSerializer(phone, context={"request": request}).data,
            status=201,
        )


class PhoneUnsoldListAPIView(PhoneAccessMixin, BaseAPIView):
    """List unsold phones with the same filters as web."""

    def get_queryset(self):
        user = self.request.user
        self.require_access(user)

        queryset = (
            models.Phone.objects.filter(is_deleted=False, is_sold=False, is_month_closed=False)
            .select_related("branch", "category", "added_by", "sold_by")
        )
        queryset = self.get_branch_queryset(queryset)
        queryset = self.apply_phone_filters(queryset)
        return queryset

    @extend_schema(
        tags=["Phone"],
        parameters=[
            *PAGINATION_PARAMETERS,
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="q", type=str, required=False),
            OpenApiParameter(name="imei", type=str, required=False),
            OpenApiParameter(name="name", type=str, required=False),
            OpenApiParameter(name="storage", type=str, required=False),
            OpenApiParameter(name="category", type=int, required=False),
        ],
        responses={200: PHONE_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PhoneListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class PhoneSoldListAPIView(PhoneAccessMixin, BaseAPIView):
    """List sold phones with the same filters as web (current month default)."""

    def get_queryset(self):
        user = self.request.user
        self.require_access(user)

        queryset = (
            models.Phone.objects.filter(
                is_deleted=False, is_sold=True, for_month_close=False
            )
            .select_related("branch", "category", "added_by", "sold_by")
        )
        queryset = self.get_branch_queryset(queryset)
        queryset = self.apply_phone_filters(queryset)

        return filter_by_month(
            queryset,
            self.request,
            field_name="sold_at",
            default_to_current=True,
        )

    @extend_schema(
        tags=["Phone"],
        parameters=[
            *YEAR_MONTH_PARAMETERS,
            OpenApiParameter(name="branch", type=int, required=False),
            OpenApiParameter(name="q", type=str, required=False),
            OpenApiParameter(name="imei", type=str, required=False),
            OpenApiParameter(name="name", type=str, required=False),
            OpenApiParameter(name="storage", type=str, required=False),
            OpenApiParameter(name="category", type=int, required=False),
        ],
        responses={200: PHONE_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = PhoneListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class PhoneSellAPIView(PhoneAccessMixin, BaseAPIView):
    """Sell a phone via `/phones/{id}/sell/`."""

    def get_object(self):
        return get_object_or_404(
            models.Phone.objects.filter(is_deleted=False).select_related(
                "branch",
                "category",
                "added_by",
                "sold_by",
            ),
            pk=self.kwargs["pk"],
        )

    @extend_schema(
        tags=["Phone"],
        request=PhoneSellSerializer,
        responses={200: PHONE_SELL_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        self.require_access(request.user)
        phone = self.get_object()
        serializer = PhoneSellSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        phone = PhoneService.sell_phone(
            phone,
            sell_price=serializer.validated_data["sell_price"],
            sold_by=request.user,
        )
        return self.success(
            PhoneListSerializer(phone, context={"request": request}).data,
            status=200,
        )


class PhoneReturnAPIView(PhoneAccessMixin, BaseAPIView):
    """Return a sold phone via `/phones/{id}/return/`."""

    def get_object(self):
        return get_object_or_404(
            models.Phone.objects.filter(is_deleted=False).select_related(
                "branch",
                "category",
                "added_by",
                "sold_by",
            ),
            pk=self.kwargs["pk"],
        )

    @extend_schema(
        tags=["Phone"],
        responses={200: PHONE_RETURN_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        self.require_access(request.user)
        phone = self.get_object()
        phone = PhoneService.return_phone(phone, returned_by=request.user)
        return self.success(
            PhoneListSerializer(phone, context={"request": request}).data,
            status=200,
        )


class PhoneDeleteAPIView(PhoneAccessMixin, BaseAPIView):
    """Delete a wrong phone via `/phones/{id}/`."""

    def get_object(self):
        return get_object_or_404(
            models.Phone.objects.filter(is_deleted=False).select_related("branch", "added_by"),
            pk=self.kwargs["pk"],
        )

    @extend_schema(
        tags=["Phone"],
        responses={200: PHONE_DELETE_RESPONSE_SCHEMA},
    )
    def delete(self, request, *args, **kwargs):
        self.require_access(request.user)
        phone = self.get_object()
        PhoneService.delete_phone(phone, deleted_by=request.user)
        return self.success({"message": _("Telefon o‘chirildi.")}, status=200)

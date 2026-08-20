from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated

import src.core.models as models
from src.api.base import BaseAPIView
from src.api.schema import PAGINATION_PARAMETERS, build_paginated_response_schema, build_success_response_schema
from src.api.serializers.support import (
    SupportRequestCreateResponseSerializer,
    SupportRequestCreateSerializer,
    SupportRequestDetailSerializer,
    SupportRequestListSerializer,
    SupportRequestMessageSerializer,
    SupportRequestReplyCreateSerializer,
)
from src.api.throttles import LandingFormThrottle
from src.services.support import create_user_reply, mark_user_read
from src.shared.permissions import HasValidXKeyOrAuthenticated


SUPPORT_REQUEST_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "SupportRequestCreateResponse",
    SupportRequestCreateResponseSerializer,
)
SUPPORT_REQUEST_LIST_RESPONSE_SCHEMA = build_paginated_response_schema(
    "SupportRequestListResponse",
    SupportRequestListSerializer,
)
SUPPORT_REQUEST_DETAIL_RESPONSE_SCHEMA = build_success_response_schema(
    "SupportRequestDetailResponse",
    SupportRequestDetailSerializer,
)
SUPPORT_REQUEST_MESSAGE_RESPONSE_SCHEMA = build_success_response_schema(
    "SupportRequestMessageResponse",
    SupportRequestMessageSerializer,
)


class SupportRequestListCreateAPIView(BaseAPIView):
    http_method_names = ["get", "post", "options"]
    throttle_classes = [LandingFormThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [HasValidXKeyOrAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = (
            models.SupportRequest.objects.filter(user=self.request.user, is_deleted=False)
            .select_related("user")
            .order_by("-last_message_at", "-added_at", "-id")
        )
        status = self.request.query_params.get("status")
        request_type = self.request.query_params.get("request_type")
        if status:
            queryset = queryset.filter(status=status)
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        return queryset

    @extend_schema(
        tags=["Support"],
        parameters=[
            *PAGINATION_PARAMETERS,
            OpenApiParameter(name="status", type=str, required=False),
            OpenApiParameter(name="request_type", type=str, required=False),
        ],
        responses={200: SUPPORT_REQUEST_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SupportRequestListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["Support"],
        request=SupportRequestCreateSerializer,
        parameters=[
            OpenApiParameter(
                name="X-Key",
                type=str,
                location=OpenApiParameter.HEADER,
                required=False,
                description="External support request key for landing site and Telegram bot.",
            )
        ],
        responses={201: SUPPORT_REQUEST_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        serializer = SupportRequestCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        support_request = serializer.save()
        return self.success(
            {
                "id": support_request.id,
                "request_type": support_request.request_type,
                "status": support_request.status,
                "message": _("Murojaatingiz qabul qilindi."),
            },
            status=201,
        )


class SupportRequestDetailAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "options"]

    def get_object(self):
        queryset = (
            models.SupportRequest.objects.filter(user=self.request.user, is_deleted=False)
            .select_related("user")
            .prefetch_related(
                Prefetch(
                    "messages",
                    queryset=models.SupportRequestMessage.objects.filter(is_deleted=False)
                    .select_related("sender")
                    .order_by("added_at", "id"),
                    to_attr="prefetched_messages",
                )
            )
        )
        return get_object_or_404(queryset, pk=self.kwargs["pk"])

    @extend_schema(
        tags=["Support"],
        responses={200: SUPPORT_REQUEST_DETAIL_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        support_request = self.get_object()
        mark_user_read(support_request)
        serializer = SupportRequestDetailSerializer(support_request, context={"request": request})
        return self.success(serializer.data)


class SupportRequestMessageCreateAPIView(BaseAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "options"]

    def get_object(self):
        return get_object_or_404(
            models.SupportRequest.objects.filter(user=self.request.user, is_deleted=False),
            pk=self.kwargs["pk"],
        )

    @extend_schema(
        tags=["Support"],
        request=SupportRequestReplyCreateSerializer,
        responses={201: SUPPORT_REQUEST_MESSAGE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        support_request = self.get_object()
        serializer = SupportRequestReplyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = create_user_reply(
            support_request,
            user=request.user,
            message=serializer.validated_data["message"],
            metadata=serializer.validated_data.get("metadata"),
        )
        return self.success(SupportRequestMessageSerializer(message).data, status=201)

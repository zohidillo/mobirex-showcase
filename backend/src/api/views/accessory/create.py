from drf_spectacular.utils import extend_schema

from src.api.base import BaseAPIView
from src.api.schema import build_success_response_schema
from src.api.serializers.accessory import AccessoryCreateSerializer, AccessoryListSerializer
from src.api.views.accessory.list import AccessoryAccessMixin
from src.shared.permissions import is_owner


ACCESSORY_CREATE_RESPONSE_SCHEMA = build_success_response_schema(
    "AccessoryCreateResponse",
    AccessoryListSerializer,
)


class AccessoryCreateAPIView(AccessoryAccessMixin, BaseAPIView):
    """Create accessories with the same branch rules as web."""

    @extend_schema(
        tags=["Accessory"],
        request=AccessoryCreateSerializer,
        responses={201: ACCESSORY_CREATE_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Create an accessory by delegating to the existing service."""
        self.require_access(request.user)
        data = request.data.copy()
        if not is_owner(request.user):
            data.pop("branch", None)
        serializer = AccessoryCreateSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        accessory = serializer.save()
        return self.success(
            AccessoryListSerializer(accessory, context={"request": request}).data,
            status=201,
        )

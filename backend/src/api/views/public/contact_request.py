from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny

from src.api.base import BaseAPIView
from src.api.schema import build_message_data_schema, build_success_response_schema
from src.api.serializers.public import (
    PublicContactRequestSerializer,
    RegionListSerializer,
    get_region_payload,
)
from src.api.throttles import PublicContactDayThrottle, PublicContactHourThrottle
from src.services.support import create_public_contact_request


PUBLIC_CONTACT_RESPONSE_SCHEMA = build_success_response_schema(
    "PublicContactRequestResponse",
    build_message_data_schema("PublicContactRequestData"),
)
REGION_LIST_RESPONSE_SCHEMA = build_success_response_schema(
    "RegionListResponse",
    RegionListSerializer,
)


class PublicContactRequestAPIView(BaseAPIView):
    """Ro‘yxatdan o‘tmagan foydalanuvchi telefon raqamini qoldiradi.

    ``AllowAny`` — X-Key yo‘q: mobil ilova ichiga joylangan sir sir emas.
    ``BaseAPIView`` xavfsiz, chunki ``IsAccountActive`` anonim so‘rovni
    o‘tkazib yuboradi; buning evaziga standart ``{success, data, error}``
    konverti, toza JSON 429 va 500‘da ichki ma’lumot sizmasligi tekinga
    keladi.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PublicContactHourThrottle, PublicContactDayThrottle]
    http_method_names = ["post", "options"]

    @extend_schema(
        tags=["Public"],
        auth=[],
        request=PublicContactRequestSerializer,
        responses={201: PUBLIC_CONTACT_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        serializer = PublicContactRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        create_public_contact_request(
            phone=serializer.validated_data["phone"],
            region=serializer.validated_data["region"],
            request=request,
        )
        return self.success(
            {"message": _("So‘rovingiz qabul qilindi.")},
            status=201,
        )


class RegionListAPIView(BaseAPIView):
    """Viloyatlar ro‘yxati — yagona manba, mobil ilova shundan oladi."""

    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["get", "options"]

    @extend_schema(
        tags=["Public"],
        auth=[],
        responses={200: REGION_LIST_RESPONSE_SCHEMA},
    )
    def get(self, request, *args, **kwargs):
        response = self.success({"regions": get_region_payload()})
        response["Cache-Control"] = "public, max-age=86400"
        return response

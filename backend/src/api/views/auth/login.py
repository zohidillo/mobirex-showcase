"""Auth login view."""

from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from drf_spectacular.utils import extend_schema, inline_serializer

from src.api.serializers.auth import AuthLoginSerializer


AUTH_LOGIN_RESPONSE_SCHEMA = inline_serializer(
    name="AuthLoginResponse",
    fields={
        "refresh": serializers.CharField(),
        "access": serializers.CharField(),
    },
)


class AuthLoginAPIView(TokenObtainPairView):
    """Return a standard SimpleJWT token pair."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    serializer_class = AuthLoginSerializer

    @extend_schema(
        tags=["Auth"],
        request=AuthLoginSerializer,
        responses={200: AUTH_LOGIN_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Return JWT tokens for valid credentials."""
        return super().post(request, *args, **kwargs)

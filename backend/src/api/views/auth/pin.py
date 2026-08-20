"""PIN API views for the mobile app."""

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, inline_serializer

from src.api.serializers.auth import ChangePinSerializer, SetPinSerializer, VerifyPinSerializer
from src.api.throttles import PinVerifyThrottle
from src.shared.demo import block_demo_user


PIN_STATUS_RESPONSE_SCHEMA = inline_serializer(
    name="PinStatusResponse",
    fields={
        "success": serializers.BooleanField(),
        "has_pin": serializers.BooleanField(),
    },
)

PIN_VERIFY_RESPONSE_SCHEMA = inline_serializer(
    name="PinVerifyResponse",
    fields={
        "success": serializers.BooleanField(),
    },
)


class SetPinAPIView(APIView):
    """Set a 4-digit PIN for the authenticated user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        operation_id="auth_pin_set",
        request=SetPinSerializer,
        responses={200: PIN_STATUS_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Hash and store a new PIN."""
        block_demo_user(request.user)
        serializer = SetPinSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"success": True, "has_pin": user.has_pin})


class VerifyPinAPIView(APIView):
    """Verify the authenticated user's existing PIN."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [PinVerifyThrottle]

    @extend_schema(
        tags=["Auth"],
        operation_id="auth_pin_verify",
        request=VerifyPinSerializer,
        responses={200: PIN_VERIFY_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Validate the submitted PIN against the stored hash."""
        serializer = VerifyPinSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response({"success": True})


class ChangePinAPIView(APIView):
    """Change the authenticated user's existing PIN."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        operation_id="auth_pin_change",
        request=ChangePinSerializer,
        responses={200: PIN_STATUS_RESPONSE_SCHEMA},
    )
    def post(self, request, *args, **kwargs):
        """Replace the current PIN after verifying the old one."""
        block_demo_user(request.user)
        serializer = ChangePinSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"success": True, "has_pin": user.has_pin})


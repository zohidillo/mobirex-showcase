"""Current-user mobile profile and settings views."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from src.api.serializers.user import MeSerializer, MeSettingsSerializer
from src.shared.demo import block_demo_user


class MeAPIView(APIView):
    """Return the authenticated user's profile and app context."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["User"],
        operation_id="me_retrieve",
        responses={200: MeSerializer},
    )
    def get(self, request, *args, **kwargs):
        """Return the current user's mobile profile."""
        return Response(MeSerializer(request.user, context={"request": request}).data)


class MeSettingsAPIView(APIView):
    """Update the authenticated user's mobile settings."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["User"],
        operation_id="me_settings_partial_update",
        request=MeSettingsSerializer,
        responses={200: MeSerializer},
    )
    def patch(self, request, *args, **kwargs):
        """Update the current user's username and/or theme."""
        new_username = request.data.get("username")
        if new_username is not None and new_username != request.user.username:
            block_demo_user(request.user)
        serializer = MeSettingsSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(MeSerializer(user, context={"request": request}).data)


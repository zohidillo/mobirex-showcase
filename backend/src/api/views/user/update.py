"""User update view."""

from drf_spectacular.utils import extend_schema

from src.api.schema import build_success_response_schema
from src.api.serializers.user import UserDetailSerializer, UserUpdateSerializer
from src.api.views.user.detail import UserDetailAPIView
from src.services.user import UserUpdateService


USER_UPDATE_RESPONSE_SCHEMA = build_success_response_schema(
    "UserUpdateResponse",
    UserDetailSerializer,
)


class UserUpdateAPIView(UserDetailAPIView):
    """Update a user. Superadmin only."""

    @extend_schema(
        tags=["User"],
        operation_id="users_partial_update",
        request=UserUpdateSerializer,
        responses={200: USER_UPDATE_RESPONSE_SCHEMA},
    )
    def patch(self, request, *args, **kwargs):
        """Partially update a user through the existing service."""
        user = self.get_object()
        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = UserUpdateService.update_user(
            user,
            validated_data=serializer.validated_data,
            updated_by=request.user,
        )
        return self.success(UserDetailSerializer(user, context={"request": request}).data)

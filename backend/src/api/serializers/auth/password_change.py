"""Password change serializer."""

from django.db import transaction
from rest_framework import serializers

from src.frontend.auth.views import UserPasswordChangeForm


class PasswordChangeSerializer(serializers.Serializer):
    """Change the authenticated user's password safely."""

    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        """Validate passwords with the existing web form."""
        form = UserPasswordChangeForm(user=self.context["request"].user, data=attrs)
        if form.is_valid():
            return attrs

        normalized_errors = {}
        for field, messages in form.errors.items():
            key = "non_field_errors" if field == "__all__" else field
            normalized_errors[key] = list(messages)
        raise serializers.ValidationError(normalized_errors)

    def save(self, **kwargs):
        """Persist the new password for the authenticated user."""
        user = self.context["request"].user
        with transaction.atomic():
            user.set_password(self.validated_data["new_password"])
            user.save()
        return user

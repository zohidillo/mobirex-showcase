"""PIN serializers for the mobile app."""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


PIN_ERROR_MESSAGE = _("PIN exactly 4 ta raqamdan iborat bo‘lishi kerak.")


class FourDigitPinField(serializers.RegexField):
    """Validate an exact 4-digit PIN without trimming or logging it."""

    def __init__(self, **kwargs):
        super().__init__(
            regex=r"^\d{4}$",
            trim_whitespace=False,
            error_messages={"invalid": PIN_ERROR_MESSAGE},
            **kwargs,
        )


class SetPinSerializer(serializers.Serializer):
    """Set or replace the authenticated user's PIN."""

    pin = FourDigitPinField(write_only=True)

    def save(self, **kwargs):
        """Hash and store the new PIN."""
        user = self.context["request"].user
        user.set_mobile_pin(self.validated_data["pin"])
        user.save()
        return user


class VerifyPinSerializer(serializers.Serializer):
    """Verify the authenticated user's PIN."""

    pin = FourDigitPinField(write_only=True)

    def validate(self, attrs):
        """Ensure a PIN exists and the submitted value matches."""
        user = self.context["request"].user
        if not user.has_pin:
            raise serializers.ValidationError({"pin": [_("PIN hali o‘rnatilmagan.")]})
        if not user.check_mobile_pin(attrs["pin"]):
            raise serializers.ValidationError({"pin": [_("PIN noto‘g‘ri.")]})
        return attrs


class ChangePinSerializer(serializers.Serializer):
    """Change the authenticated user's PIN."""

    old_pin = FourDigitPinField(write_only=True)
    new_pin = FourDigitPinField(write_only=True)

    def validate(self, attrs):
        """Require the old PIN before replacing it."""
        user = self.context["request"].user
        if not user.has_pin:
            raise serializers.ValidationError({"old_pin": [_("PIN hali o‘rnatilmagan.")]})
        if not user.check_mobile_pin(attrs["old_pin"]):
            raise serializers.ValidationError({"old_pin": [_("Eski PIN noto‘g‘ri.")]})
        return attrs

    def save(self, **kwargs):
        """Hash and persist the replacement PIN."""
        user = self.context["request"].user
        user.set_mobile_pin(self.validated_data["new_pin"])
        user.save()
        return user


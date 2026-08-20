"""Account deletion serializer."""

from rest_framework import serializers


class AccountDeleteSerializer(serializers.Serializer):
    """Optional refresh token to blacklist on self-service deletion."""

    refresh = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Joriy refresh token — yuborilsa blacklist qilinadi.",
    )

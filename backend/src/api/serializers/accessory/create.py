from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

import src.core.models as models
from src.services.accessory import AccessoryCreateService
from src.shared.permissions import is_accessory_seller, is_owner
from src.shared.validators import validate_branch_access, validate_positive_amount


class AccessoryCreateSerializer(serializers.ModelSerializer):
    """Create accessories with web-equivalent validation."""

    branch = serializers.PrimaryKeyRelatedField(
        queryset=models.Branch.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.Accessory
        fields = [
            "branch",
            "name",
            "category",
            "stock",
            "unit_cost",
            "image",
        ]
        validators = []

    def validate_stock(self, value):
        """Validate the initial stock amount."""
        return int(validate_positive_amount(value))

    def validate_unit_cost(self, value):
        """Validate the accessory unit cost."""
        return validate_positive_amount(value)

    def validate(self, attrs):
        """Validate branch selection against the acting user."""
        user = self.context["request"].user
        branch = attrs.get("branch")

        if is_owner(user):
            if not branch:
                raise serializers.ValidationError({"branch": _("Filial tanlash shart.")})
            validate_branch_access(user, branch)
            return attrs

        if not is_accessory_seller(user):
            raise PermissionDenied(_("Ruxsat yo‘q."))

        attrs.pop("branch", None)
        return attrs

    def create(self, validated_data):
        """Create an accessory through the existing service."""
        user = self.context["request"].user

        if is_owner(user):
            branch = validated_data["branch"]
        else:
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch:
                raise PermissionDenied(_("Filialga ruxsat yo‘q."))
            validated_data["branch"] = branch

        validate_branch_access(user, branch)
        return AccessoryCreateService.create_accessory(validated_data, added_by=user)

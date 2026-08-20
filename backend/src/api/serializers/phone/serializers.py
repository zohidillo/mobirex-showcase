from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

import src.core.models as models
from src.services.phone import PhoneCreateService
from src.shared.permissions import is_owner, is_phone_seller
from src.shared.validators import validate_branch_access


@extend_schema_serializer(component_name="PhoneInventoryCategory")
class PhoneCategorySerializer(serializers.ModelSerializer):
    """Serialize phone category details."""

    class Meta:
        model = models.PhoneCategory
        fields = ["id", "name", "description"]


@extend_schema_serializer(component_name="PhoneInventoryBranch")
class BranchSerializer(serializers.ModelSerializer):
    """Serialize branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


@extend_schema_serializer(component_name="PhoneInventoryUserSummary")
class UserSummarySerializer(serializers.ModelSerializer):
    """Serialize minimal user details."""

    class Meta:
        model = models.User
        fields = ["id", "username"]


class PhoneListSerializer(serializers.ModelSerializer):
    """Serialize phone inventory details."""

    branch = BranchSerializer(read_only=True)
    category = PhoneCategorySerializer(read_only=True)
    added_by = UserSummarySerializer(read_only=True)
    sold_by = UserSummarySerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    category_id = serializers.IntegerField(read_only=True)
    added_by_id = serializers.IntegerField(read_only=True)
    sold_by_id = serializers.IntegerField(read_only=True)
    profit = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    is_profitable = serializers.BooleanField(read_only=True)

    class Meta:
        model = models.Phone
        fields = [
            "id",
            "name",
            "category",
            "category_id",
            "branch",
            "branch_id",
            "imei",
            "storage",
            "color",
            "from_by",
            "cost_price",
            "sell_price",
            "is_sold",
            "for_month_close",
            "added_by",
            "added_by_id",
            "sold_by",
            "sold_by_id",
            "profit",
            "is_profitable",
            "added_at",
            "updated_at",
            "sold_at",
        ]


class PhoneCreateSerializer(serializers.ModelSerializer):
    """Validate phone creation payloads."""

    branch = serializers.PrimaryKeyRelatedField(
        queryset=models.Branch.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.Phone
        fields = [
            "branch",
            "name",
            "category",
            "storage",
            "color",
            "from_by",
            "imei",
            "cost_price",
        ]

    def validate(self, attrs):
        """Validate branch selection against the acting user."""
        user = self.context["request"].user
        branch = attrs.get("branch")

        if is_owner(user):
            if not branch:
                raise serializers.ValidationError({"branch": _("Filial tanlash shart.")})
            validate_branch_access(user, branch)
            return attrs

        if not is_phone_seller(user):
            raise PermissionDenied(_("Ruxsat yo‘q."))

        attrs.pop("branch", None)
        return attrs

    def create(self, validated_data):
        """Create a phone through the existing service."""
        user = self.context["request"].user

        if is_owner(user):
            branch = validated_data["branch"]
        else:
            branch = user.get_primary_branch("PHONE_SELLER")
            if not branch:
                raise PermissionDenied(_("Filialga ruxsat yo‘q."))
            validated_data["branch"] = branch

        validate_branch_access(user, branch)
        return PhoneCreateService.create_phone(validated_data, added_by=user)


class PhoneSellSerializer(serializers.ModelSerializer):
    """Validate phone sell payloads."""

    class Meta:
        model = models.Phone
        fields = ["sell_price"]

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

import src.core.models as models


@extend_schema_serializer(component_name="AccessoryInventoryCategory")
class AccessoryCategorySerializer(serializers.ModelSerializer):
    """Serialize accessory category details."""

    class Meta:
        model = models.AccessoryCategory
        fields = ["id", "name", "description"]


@extend_schema_serializer(component_name="AccessoryInventoryBranch")
class BranchSerializer(serializers.ModelSerializer):
    """Serialize branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


@extend_schema_serializer(component_name="AccessoryInventoryUserSummary")
class UserSummarySerializer(serializers.ModelSerializer):
    """Serialize minimal user details."""

    class Meta:
        model = models.User
        fields = ["id", "username"]


class AccessoryListSerializer(serializers.ModelSerializer):
    """List accessories with template-visible fields."""

    branch = BranchSerializer(read_only=True)
    category = AccessoryCategorySerializer(read_only=True)
    added_by = UserSummarySerializer(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    category_id = serializers.IntegerField(read_only=True)
    added_by_id = serializers.IntegerField(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Accessory
        fields = [
            "id",
            "name",
            "category",
            "category_id",
            "branch",
            "branch_id",
            "unit_cost",
            "stock",
            "image",
            "image_url",
            "added_by",
            "added_by_id",
            "is_active",
            "added_at",
            "updated_at",
        ]

    def get_image_url(self, obj) -> str | None:
        """Return the accessory image URL when available."""
        if not obj.image:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

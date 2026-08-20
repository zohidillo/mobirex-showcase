"""Journal list serializers."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers

import src.core.models as models


MODEL_DISPLAY_MAP = {
    "phone": "Telefon",
    "accessory": "Aksessuar",
    "accessorysale": "Aksessuar savdosi",
    "debt": "Qarz",
    "debtpayment": "Qarz to'lovi",
    "expense": "Xarajat",
    "salary": "Oylik",
    "extraprofit": "Qo'shimcha foyda",
    "branch": "Filial",
    "branchuser": "Filial roli",
    "subscription": "Obuna",
    "subscriptionpayment": "Obuna to'lovi",
    "payment": "To'lov",
    "transactionlog": "Tranzaksiya jurnali",
    "phonecapital": "Telefon kapitali",
    "accessorycapital": "Aksessuar kapitali",
    "journal": "Jurnal",
    "user": "Foydalanuvchi",
}


class JournalUserSerializer(serializers.ModelSerializer):
    """Serialize journal user details."""

    class Meta:
        model = models.User
        fields = ["id", "username"]


class JournalBranchSerializer(serializers.ModelSerializer):
    """Serialize journal branch details."""

    class Meta:
        model = models.Branch
        fields = ["id", "name", "address", "is_active"]


class JournalListSerializer(serializers.ModelSerializer):
    """List journal entries. Owner sees branch data. Seller sees own data."""

    user = JournalUserSerializer(read_only=True)
    branch = JournalBranchSerializer(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    branch_id = serializers.IntegerField(read_only=True)
    action_type = serializers.CharField(source="action", read_only=True)
    action_display = serializers.ReadOnlyField(source="get_action_display")
    related_object = serializers.SerializerMethodField()
    related_object_label = serializers.SerializerMethodField()
    related_model = serializers.CharField(source="model_name", read_only=True)
    related_model_display = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="added_at", read_only=True)

    class Meta:
        model = models.Journal
        fields = [
            "id",
            "action_type",
            "action_display",
            "amount",
            "user",
            "user_id",
            "branch",
            "branch_id",
            "branch_name",
            "related_model",
            "related_model_display",
            "related_object",
            "related_object_label",
            "object_id",
            "object_repr",
            "created_at",
            "added_at",
        ]

    @extend_schema_field(
        inline_serializer(
            name="JournalRelatedObject",
            fields={
                "model_name": serializers.CharField(),
                "object_id": serializers.IntegerField(),
                "object_repr": serializers.CharField(),
            },
        )
    )
    def get_related_object(self, obj):
        """Return a compact related object description."""
        return {
            "model_name": obj.model_name,
            "object_id": obj.object_id,
            "object_repr": obj.object_repr or self.get_related_object_label(obj),
        }

    def get_related_object_label(self, obj) -> str:
        """Return the template-visible related object label."""
        data = obj.new_data or obj.old_data or {}
        return (
            obj.object_repr
            or data.get("name")
            or data.get("title")
            or data.get("username")
            or data.get("imei")
            or data.get("person_name")
            or "-"
        )

    def get_related_model_display(self, obj) -> str:
        """Return the template-style model label."""
        return MODEL_DISPLAY_MAP.get(obj.model_name, obj.model_name)

    @extend_schema_field(OpenApiTypes.NUMBER)
    def get_amount(self, obj):
        """Return the main amount-like value when present."""
        data = obj.new_data or obj.old_data or {}
        for field_name in ("amount", "sell_price", "total_price"):
            value = data.get(field_name)
            if value is not None:
                return value
        return None

    def get_branch_name(self, obj) -> str:
        """Return the journal branch name."""
        return obj.branch.name if obj.branch else "-"

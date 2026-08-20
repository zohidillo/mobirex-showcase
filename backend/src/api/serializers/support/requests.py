from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

import src.core.models as models
from src.services.support import create_support_request
from src.shared.demo import block_demo_user


class SupportRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SupportRequest
        fields = [
            "request_type",
            "source",
            "full_name",
            "phone",
            "message",
            "metadata",
        ]
        extra_kwargs = {
            "source": {"required": False},
            "metadata": {"required": False},
            "message": {"allow_blank": True, "required": False},
        }

    def validate_metadata(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Metadata obyekt bo‘lishi kerak."))
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not attrs.get("source"):
            attrs["source"] = (
                models.SupportRequest.Source.MOBILE_APP
                if user and user.is_authenticated
                else models.SupportRequest.Source.LANDING_SITE
            )
        if attrs.get("request_type") == models.SupportRequest.RequestType.ACCOUNT_DELETE:
            block_demo_user(user)
            if not attrs.get("phone") and user and getattr(user, "phone", None):
                attrs["phone"] = user.phone
            if not attrs.get("phone"):
                raise serializers.ValidationError(
                    {"phone": _("Account o‘chirish murojaati uchun telefon raqami shart.")}
                )
            if not attrs.get("message"):
                attrs["message"] = "Accountni o‘chirish so‘rovi yuborildi."
        elif not attrs.get("message"):
            raise serializers.ValidationError({"message": _("Xabar kiritilishi shart.")})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return create_support_request(validated_data=validated_data, user=user, request=request)


class SupportRequestCreateResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    request_type = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField()


class SupportRequestMessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    created_at = serializers.DateTimeField(source="added_at", read_only=True)

    class Meta:
        model = models.SupportRequestMessage
        fields = [
            "id",
            "sender_type",
            "sender_username",
            "message",
            "created_at",
            "added_at",
        ]
        read_only_fields = fields


class SupportRequestListSerializer(serializers.ModelSerializer):
    request_type_display = serializers.CharField(source="get_request_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    message = serializers.SerializerMethodField()
    unread_for_user = serializers.BooleanField(read_only=True)

    class Meta:
        model = models.SupportRequest
        fields = [
            "id",
            "request_type",
            "request_type_display",
            "source",
            "status",
            "status_display",
            "phone",
            "message",
            "last_message_at",
            "last_admin_reply_at",
            "unread_for_user",
            "added_at",
            "updated_at",
        ]

    def get_message(self, obj):
        message = obj.message or ""
        return message[:160]


class SupportRequestDetailSerializer(serializers.ModelSerializer):
    request_type_display = serializers.CharField(source="get_request_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    unread_for_user = serializers.BooleanField(read_only=True)
    messages = serializers.SerializerMethodField()

    class Meta:
        model = models.SupportRequest
        fields = [
            "id",
            "request_type",
            "request_type_display",
            "source",
            "status",
            "status_display",
            "full_name",
            "phone",
            "message",
            "metadata",
            "last_message_at",
            "last_admin_reply_at",
            "last_user_message_at",
            "user_read_at",
            "unread_for_user",
            "added_at",
            "updated_at",
            "messages",
        ]

    @extend_schema_field(SupportRequestMessageSerializer(many=True))
    def get_messages(self, obj):
        messages = getattr(obj, "prefetched_messages", None)
        if messages is None:
            messages = (
                obj.messages.filter(is_deleted=False)
                .select_related("sender")
                .order_by("added_at", "id")
            )
        return SupportRequestMessageSerializer(messages, many=True).data


class SupportRequestReplyCreateSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False, trim_whitespace=True)
    metadata = serializers.JSONField(required=False)

    def validate_metadata(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Metadata obyekt bo‘lishi kerak."))
        return value

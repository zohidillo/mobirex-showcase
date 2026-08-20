"""Phone category serializers."""

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

import src.core.models as models


@extend_schema_serializer(component_name="AdminPhoneCategory")
class PhoneCategorySerializer(serializers.ModelSerializer):
    """Serialize phone categories visible in admin list."""

    class Meta:
        model = models.PhoneCategory
        fields = ["id", "name", "added_at"]

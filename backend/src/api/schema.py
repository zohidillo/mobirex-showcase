"""Reusable OpenAPI schema helpers for API views."""

from rest_framework import serializers

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, inline_serializer


PAGE_PARAMETER = OpenApiParameter(
    name="page",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Pagination page number.",
)
YEAR_PARAMETER = OpenApiParameter(
    name="year",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Year filter. Use together with month.",
)
MONTH_PARAMETER = OpenApiParameter(
    name="month",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Month filter from 1 to 12. Use together with year.",
)
FROM_DATE_PARAMETER = OpenApiParameter(
    name="from_date",
    type=OpenApiTypes.DATE,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Start date filter in YYYY-MM-DD format.",
)
TO_DATE_PARAMETER = OpenApiParameter(
    name="to_date",
    type=OpenApiTypes.DATE,
    location=OpenApiParameter.QUERY,
    required=False,
    description="End date filter in YYYY-MM-DD format.",
)

PAGINATION_PARAMETERS = [PAGE_PARAMETER]
YEAR_MONTH_PARAMETERS = [PAGE_PARAMETER, YEAR_PARAMETER, MONTH_PARAMETER]
YEAR_MONTH_RANGE_PARAMETERS = [
    PAGE_PARAMETER,
    YEAR_PARAMETER,
    MONTH_PARAMETER,
    FROM_DATE_PARAMETER,
    TO_DATE_PARAMETER,
]


def _as_schema_component(component, *, many=False):
    """Return a serializer or field instance that Spectacular can render."""
    if isinstance(component, type) and issubclass(component, serializers.BaseSerializer):
        return component(many=many)
    if isinstance(component, serializers.BaseSerializer):
        if getattr(component, "many", False) == many:
            return component
        return component.__class__(many=many)
    if isinstance(component, serializers.Field):
        return component
    raise TypeError(f"Unsupported schema component: {component!r}")


def build_success_response_schema(name, data_schema):
    """Wrap a response payload in the project's standard success envelope."""
    return inline_serializer(
        name=name,
        fields={
            "success": serializers.BooleanField(default=True),
            "data": _as_schema_component(data_schema),
            "error": serializers.CharField(allow_null=True),
        },
    )


def build_paginated_response_schema(name, item_schema, *, extra_fields=None):
    """Wrap a list serializer in the project's paginated data structure."""
    fields = {
        "count": serializers.IntegerField(),
        "next": serializers.CharField(allow_null=True),
        "previous": serializers.CharField(allow_null=True),
        "results": _as_schema_component(item_schema, many=True),
    }
    if extra_fields:
        fields.update(extra_fields)
    return inline_serializer(
        name=name,
        fields={
            "success": serializers.BooleanField(default=True),
            "data": inline_serializer(name=f"{name}Data", fields=fields),
        },
    )


def build_message_data_schema(name):
    """Return a small `{message: ...}` serializer for success payloads."""
    return inline_serializer(
        name=name,
        fields={
            "message": serializers.CharField(),
        },
    )

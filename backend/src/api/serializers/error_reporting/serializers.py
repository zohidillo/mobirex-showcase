from rest_framework import serializers

import src.core.models as models


class ErrorReportSerializer(serializers.Serializer):
    severity = serializers.ChoiceField(
        choices=models.ErrorReport.Severity.choices,
        default=models.ErrorReport.Severity.ERROR,
        required=False,
    )
    kind = serializers.ChoiceField(
        choices=models.ErrorReport.Kind.choices,
        default=models.ErrorReport.Kind.EXCEPTION,
        required=False,
    )
    error_type = serializers.CharField(max_length=255)
    error_message = serializers.CharField()
    stack_trace = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    request_path = serializers.CharField(max_length=500, required=False, allow_blank=True, allow_null=True)
    request_method = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    status_code = serializers.IntegerField(required=False, allow_null=True)
    app_version = serializers.CharField(max_length=32, required=False, allow_blank=True, allow_null=True)
    platform = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    context = serializers.DictField(required=False, default=dict)

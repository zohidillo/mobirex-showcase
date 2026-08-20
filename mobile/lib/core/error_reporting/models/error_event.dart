class ErrorEvent {
  final String severity;
  final String kind;
  final String errorType;
  final String errorMessage;
  final String? stackTrace;
  final String? requestPath;
  final String? requestMethod;
  final int? statusCode;
  final String appVersion;
  final String platform;
  final Map<String, dynamic> context;
  final DateTime occurredAt;
  final String fingerprint;

  const ErrorEvent({
    required this.severity,
    required this.kind,
    required this.errorType,
    required this.errorMessage,
    this.stackTrace,
    this.requestPath,
    this.requestMethod,
    this.statusCode,
    required this.appVersion,
    required this.platform,
    required this.context,
    required this.occurredAt,
    required this.fingerprint,
  });

  Map<String, dynamic> toJson() => {
        'severity': severity,
        'kind': kind,
        'error_type': errorType,
        'error_message': errorMessage,
        if (stackTrace != null) 'stack_trace': stackTrace,
        if (requestPath != null) 'request_path': requestPath,
        if (requestMethod != null) 'request_method': requestMethod,
        if (statusCode != null) 'status_code': statusCode,
        'app_version': appVersion,
        'platform': platform,
        'context': context,
      };

  Map<String, dynamic> toQueueJson() => {
        ...toJson(),
        'occurred_at': occurredAt.toIso8601String(),
        'fingerprint': fingerprint,
      };

  factory ErrorEvent.fromQueueJson(Map<String, dynamic> json) => ErrorEvent(
        severity: json['severity'] as String,
        kind: json['kind'] as String,
        errorType: json['error_type'] as String,
        errorMessage: json['error_message'] as String,
        stackTrace: json['stack_trace'] as String?,
        requestPath: json['request_path'] as String?,
        requestMethod: json['request_method'] as String?,
        statusCode: json['status_code'] as int?,
        appVersion: json['app_version'] as String,
        platform: json['platform'] as String,
        context: (json['context'] as Map?)?.cast<String, dynamic>() ?? {},
        occurredAt: DateTime.parse(json['occurred_at'] as String),
        fingerprint: json['fingerprint'] as String,
      );
}

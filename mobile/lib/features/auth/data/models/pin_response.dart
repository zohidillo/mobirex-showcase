class PinResponse {
  final bool success;
  final bool? hasPin;
  final bool? pinEnabled;

  const PinResponse({required this.success, this.hasPin, this.pinEnabled});

  factory PinResponse.fromJson(Map<String, dynamic> json) => PinResponse(
    success: json['success'] as bool? ?? false,
    hasPin: json['has_pin'] as bool?,
    pinEnabled: json['pin_enabled'] as bool?,
  );
}

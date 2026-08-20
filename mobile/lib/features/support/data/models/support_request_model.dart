import 'support_message_model.dart';

class SupportRequest {
  final int id;
  final String requestType;
  final String requestTypeDisplay;
  final String source;
  final String status;
  final String statusDisplay;
  final String phone;
  final String message;
  final bool unreadForUser;
  final DateTime? lastMessageAt;
  final DateTime? lastAdminReplyAt;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<SupportMessage> messages;

  const SupportRequest({
    required this.id,
    required this.requestType,
    required this.requestTypeDisplay,
    required this.source,
    required this.status,
    required this.statusDisplay,
    required this.phone,
    required this.message,
    required this.unreadForUser,
    this.lastMessageAt,
    this.lastAdminReplyAt,
    required this.createdAt,
    required this.updatedAt,
    this.messages = const [],
  });

  factory SupportRequest.fromJson(Map<String, dynamic> json) => SupportRequest(
    id: json['id'] as int,
    requestType: json['request_type'] as String? ?? '',
    requestTypeDisplay: json['request_type_display'] as String? ?? '',
    source: json['source'] as String? ?? '',
    status: json['status'] as String? ?? '',
    statusDisplay: json['status_display'] as String? ?? '',
    phone: json['phone'] as String? ?? '',
    message: json['message'] as String? ?? '',
    unreadForUser: json['unread_for_user'] as bool? ?? false,
    lastMessageAt: _parseDate(json['last_message_at']),
    lastAdminReplyAt: _parseDate(json['last_admin_reply_at']),
    createdAt:
        _parseDate(json['created_at'] ?? json['added_at']) ?? DateTime.now(),
    updatedAt: _parseDate(json['updated_at']) ?? DateTime.now(),
    messages: (json['messages'] as List<dynamic>? ?? [])
        .map((e) => SupportMessage.fromJson(e as Map<String, dynamic>))
        .toList(),
  );

  static DateTime? _parseDate(dynamic val) {
    if (val == null) return null;
    return DateTime.tryParse(val as String);
  }

  SupportRequest copyWith({
    bool? unreadForUser,
    List<SupportMessage>? messages,
  }) => SupportRequest(
    id: id,
    requestType: requestType,
    requestTypeDisplay: requestTypeDisplay,
    source: source,
    status: status,
    statusDisplay: statusDisplay,
    phone: phone,
    message: message,
    unreadForUser: unreadForUser ?? this.unreadForUser,
    lastMessageAt: lastMessageAt,
    lastAdminReplyAt: lastAdminReplyAt,
    createdAt: createdAt,
    updatedAt: updatedAt,
    messages: messages ?? this.messages,
  );
}

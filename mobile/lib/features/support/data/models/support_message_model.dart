class SupportMessage {
  final int id;
  final String senderType;
  final String? senderUsername;
  final String message;
  final DateTime createdAt;

  const SupportMessage({
    required this.id,
    required this.senderType,
    this.senderUsername,
    required this.message,
    required this.createdAt,
  });

  factory SupportMessage.fromJson(Map<String, dynamic> json) => SupportMessage(
    id: json['id'] as int,
    senderType: json['sender_type'] as String? ?? 'USER',
    senderUsername: json['sender_username'] as String?,
    message: json['message'] as String? ?? '',
    createdAt:
        DateTime.tryParse(
          (json['created_at'] ?? json['added_at'] ?? '') as String,
        ) ??
        DateTime.now(),
  );
}

class Breadcrumb {
  final DateTime timestamp;
  final String category;
  final String message;
  final Map<String, dynamic> data;

  const Breadcrumb({
    required this.timestamp,
    required this.category,
    required this.message,
    this.data = const {},
  });

  Map<String, dynamic> toJson() => {
        'timestamp': timestamp.toIso8601String(),
        'category': category,
        'message': message,
        if (data.isNotEmpty) 'data': data,
      };
}

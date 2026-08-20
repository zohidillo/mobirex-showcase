import 'models/breadcrumb.dart';

class BreadcrumbsTracker {
  static const int maxSize = 20;
  static final List<Breadcrumb> _buffer = [];

  static void add(Breadcrumb b) {
    _buffer.add(b);
    if (_buffer.length > maxSize) _buffer.removeAt(0);
  }

  static void addNavigation({required String from, required String to}) {
    add(Breadcrumb(
      timestamp: DateTime.now(),
      category: 'navigation',
      message: '$from → $to',
    ));
  }

  static void addHttp({
    required String method,
    required String path,
    int? statusCode,
    int? durationMs,
  }) {
    add(Breadcrumb(
      timestamp: DateTime.now(),
      category: 'http',
      message: '$method $path',
      data: {
        'status': ?statusCode,
        'duration_ms': ?durationMs,
      },
    ));
  }

  static void addUi(String message, [Map<String, dynamic>? data]) {
    add(Breadcrumb(
      timestamp: DateTime.now(),
      category: 'ui',
      message: message,
      data: data ?? const {},
    ));
  }

  static void addLog(String message) {
    add(Breadcrumb(
      timestamp: DateTime.now(),
      category: 'log',
      message: message,
    ));
  }

  static List<Map<String, dynamic>> toList() =>
      _buffer.map((b) => b.toJson()).toList();

  static void clear() => _buffer.clear();
}

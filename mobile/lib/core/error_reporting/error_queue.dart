import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'models/error_event.dart';

class ErrorQueue {
  static const String _key = 'mobirex_error_queue_v1';
  static const int maxQueueSize = 50;

  static Future<void> enqueue(ErrorEvent event) async {
    final prefs = await SharedPreferences.getInstance();
    final list = _load(prefs);
    if (list.length >= maxQueueSize) list.removeAt(0);
    list.add(jsonEncode(event.toQueueJson()));
    await prefs.setStringList(_key, list);
  }

  static Future<List<ErrorEvent>> drain() async {
    final prefs = await SharedPreferences.getInstance();
    final list = _load(prefs);
    return list
        .map((s) {
          try {
            return ErrorEvent.fromQueueJson(
                jsonDecode(s) as Map<String, dynamic>);
          } catch (_) {
            return null;
          }
        })
        .whereType<ErrorEvent>()
        .toList();
  }

  static Future<void> remove(ErrorEvent event) async {
    final prefs = await SharedPreferences.getInstance();
    final list = _load(prefs);
    final id = '${event.fingerprint}_${event.occurredAt.toIso8601String()}';
    list.removeWhere((s) {
      try {
        final m = jsonDecode(s) as Map<String, dynamic>;
        return '${m['fingerprint']}_${m['occurred_at']}' == id;
      } catch (_) {
        return false;
      }
    });
    await prefs.setStringList(_key, list);
  }

  static Future<int> size() async {
    final prefs = await SharedPreferences.getInstance();
    return _load(prefs).length;
  }

  static List<String> _load(SharedPreferences prefs) =>
      List<String>.from(prefs.getStringList(_key) ?? []);
}

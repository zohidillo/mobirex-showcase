import 'dart:convert';

import 'package:flutter/foundation.dart';

const _sensitiveKeys = {
  'access',
  'refresh',
  'token',
  'access_token',
  'refresh_token',
  'password',
  'old_password',
  'new_password',
  'new_password_confirm',
  'pin',
  'old_pin',
  'new_pin',
  'authorization',
};

void safeAuthLog(String message) {
  if (kDebugMode || kProfileMode) {
    debugPrint('[auth] $message');
  }
}

String responseKeysForLog(dynamic data) {
  if (data is Map) {
    return data.keys.map((key) => key.toString()).toList().toString();
  }
  return data.runtimeType.toString();
}

String safeResponseBodyForLog(dynamic data) {
  if (data == null) return 'null';

  if (data is String) {
    final trimmed = data.trim();
    final prefix = trimmed.length > 300 ? trimmed.substring(0, 300) : trimmed;
    if (looksLikeHtml(data)) {
      return 'HTML response (${data.length} chars): $prefix';
    }
    return prefix;
  }

  try {
    final encoded = jsonEncode(_sanitizeForLog(data));
    return encoded.length > 800 ? '${encoded.substring(0, 800)}...' : encoded;
  } catch (_) {
    return data.runtimeType.toString();
  }
}

bool looksLikeHtml(dynamic data) {
  if (data is! String) return false;
  final lower = data.trimLeft().toLowerCase();
  return lower.startsWith('<!doctype html') ||
      lower.startsWith('<html') ||
      lower.contains('<body') ||
      lower.contains('<head');
}

dynamic _sanitizeForLog(dynamic value) {
  if (value is Map) {
    return value.map((key, child) {
      final normalizedKey = key.toString().toLowerCase();
      final isSensitive = _sensitiveKeys.any(normalizedKey.contains);
      return MapEntry(
        key.toString(),
        isSensitive ? '<redacted>' : _sanitizeForLog(child),
      );
    });
  }

  if (value is List) {
    return value.map(_sanitizeForLog).toList();
  }

  return value;
}

import 'package:flutter/foundation.dart';

class RateLimiter {
  static final Map<String, DateTime> _lastSent = {};
  static int _globalCountThisMinute = 0;
  static DateTime? _minuteWindowStart;

  static const int _maxPerMinute = 5;
  static const Duration _fingerprintCooldown = Duration(minutes: 5);

  static bool shouldSend(String fingerprint) {
    final now = DateTime.now();

    // Global bucket: max 5 per minute
    if (_minuteWindowStart == null ||
        now.difference(_minuteWindowStart!) >= const Duration(minutes: 1)) {
      _minuteWindowStart = now;
      _globalCountThisMinute = 0;
    }
    if (_globalCountThisMinute >= _maxPerMinute) return false;

    // Per-fingerprint cooldown
    final last = _lastSent[fingerprint];
    if (last != null && now.difference(last) < _fingerprintCooldown) {
      return false;
    }
    return true;
  }

  static void recordSent(String fingerprint) {
    _lastSent[fingerprint] = DateTime.now();
    _globalCountThisMinute++;
  }

  @visibleForTesting
  static void reset() {
    _lastSent.clear();
    _globalCountThisMinute = 0;
    _minuteWindowStart = null;
  }
}

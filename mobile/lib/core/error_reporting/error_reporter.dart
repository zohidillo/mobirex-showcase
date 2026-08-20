import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../config/app_config.dart';
import '../storage/secure_storage.dart';
import 'breadcrumbs.dart';
import 'device_context.dart';
import 'error_queue.dart';
import 'fingerprint.dart';
import 'models/error_event.dart';
import 'rate_limiter.dart';

class ErrorReporter {
  static late Dio _dio;
  static int? _userId;
  static String? _username;
  static List<String> _roles = [];
  static List<String> _branches = [];
  static bool _initialized = false;
  static StreamSubscription<List<ConnectivityResult>>? _connectivitySub;

  static Future<void> initialize() async {
    if (_initialized) return;
    await DeviceContextCollector.initialize();
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ));
    _initialized = true;
    unawaited(_drainQueueInBackground());
    _connectivitySub = Connectivity().onConnectivityChanged.listen((results) {
      if (results.any((r) => r != ConnectivityResult.none)) {
        unawaited(_drainQueueInBackground());
      }
    });
  }

  static void setUser({
    required int id,
    required String username,
    required List<String> roles,
    required List<String> branches,
  }) {
    _userId = id;
    _username = username;
    _roles = roles;
    _branches = branches;
  }

  static void clearUser() {
    _userId = null;
    _username = null;
    _roles = [];
    _branches = [];
  }

  static Future<void> report(
    Object error,
    StackTrace? stack, {
    String severity = 'ERROR',
    String kind = 'EXCEPTION',
    String? requestPath,
    String? requestMethod,
    int? statusCode,
    Map<String, dynamic>? extraContext,
  }) async {
    try {
      final errorType = error.runtimeType.toString();
      final fingerprint = computeFingerprint(
        errorType: errorType,
        requestPath: requestPath,
        statusCode: statusCode,
      );

      if (!RateLimiter.shouldSend(fingerprint)) return;

      final deviceCtx = DeviceContextCollector.snapshot();
      final event = ErrorEvent(
        severity: severity,
        kind: kind,
        errorType: errorType,
        errorMessage: error.toString(),
        stackTrace: stack?.toString(),
        requestPath: requestPath,
        requestMethod: requestMethod,
        statusCode: statusCode,
        appVersion: deviceCtx['app_version'] as String,
        platform: deviceCtx['platform'] as String,
        context: {
          ...deviceCtx,
          if (_userId != null) 'user_id': _userId,
          if (_username != null) 'username': _username,
          if (_roles.isNotEmpty) 'roles': _roles,
          if (_branches.isNotEmpty) 'branches': _branches,
          'breadcrumbs': BreadcrumbsTracker.toList(),
          ...?extraContext,
        },
        occurredAt: DateTime.now(),
        fingerprint: fingerprint,
      );

      RateLimiter.recordSent(fingerprint);

      final ok = await _trySend(event);
      if (!ok) await ErrorQueue.enqueue(event);
    } catch (_) {
      // ErrorReporter o'zi hech qachon throw qilmaydi
    }
  }

  static Future<void> reportFatal(Object error, StackTrace? stack) =>
      report(error, stack, severity: 'CRITICAL');

  static Future<bool> _trySend(ErrorEvent event) async {
    try {
      final token = await SecureStorageService.getAccessToken();
      if (token == null) return false;
      await _dio.post(
        '/api/error-report/',
        data: event.toJson(),
        options: Options(headers: {'Authorization': 'Bearer $token'}),
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  static Future<void> _drainQueueInBackground() async {
    final events = await ErrorQueue.drain();
    for (final event in events) {
      final ok = await _trySend(event);
      if (ok) {
        await ErrorQueue.remove(event);
      } else {
        break;
      }
    }
  }

  @visibleForTesting
  static int? get userId => _userId;

  @visibleForTesting
  static String? get username => _username;

  @visibleForTesting
  static List<String> get roles => List.unmodifiable(_roles);

  @visibleForTesting
  static void resetForTest() {
    _initialized = false;
    _userId = null;
    _username = null;
    _roles = [];
    _branches = [];
    _connectivitySub?.cancel();
    _connectivitySub = null;
    BreadcrumbsTracker.clear();
  }
}

import 'package:dio/dio.dart';
import '../../config/app_config.dart';
import '../../constants/api_constants.dart';
import '../../storage/secure_storage.dart';
import '../session_notifier.dart';

class AuthInterceptor extends QueuedInterceptorsWrapper {
  // Separate Dio instance to avoid interceptor recursion on refresh calls.
  final Dio _refreshDio = Dio(BaseOptions(baseUrl: baseUrl));

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await SecureStorageService.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // Billing block (402) is handled in its OWN branch and never touches the
    // 401 refresh flow below: no token refresh, no logout. We just raise the
    // accountBlocked signal so the router moves to the blocked screen, then
    // let the error propagate normally.
    if (_isAccountBlocked(err)) {
      accountBlockedNotifier.value = true;
      handler.next(err);
      return;
    }

    final isUnauthorized = err.response?.statusCode == 401;
    final isRefreshPath = err.requestOptions.path.contains(
      ApiConstants.refresh,
    );
    final isLoginPath = err.requestOptions.path.contains(ApiConstants.login);

    if (isUnauthorized && !isRefreshPath && !isLoginPath) {
      try {
        final refreshToken = await SecureStorageService.getRefreshToken();
        if (refreshToken == null) {
          await _expireSession(err, handler);
          return;
        }

        final response = await _refreshDio.post(
          ApiConstants.refresh,
          data: {'refresh': refreshToken},
        );

        final newToken = response.data['access'] as String;
        await SecureStorageService.saveAccessToken(newToken);
        final newRefresh = response.data['refresh'];
        if (newRefresh != null) {
          await SecureStorageService.saveRefreshToken(newRefresh as String);
        }

        final opts = err.requestOptions;
        opts.headers['Authorization'] = 'Bearer $newToken';
        final retryResponse = await _refreshDio.fetch(opts);
        handler.resolve(retryResponse);
      } catch (_) {
        await _expireSession(err, handler);
      }
    } else {
      handler.next(err);
    }
  }

  /// True only for HTTP 402 whose body carries error.code == "account_blocked"
  /// (the backend billing-block contract). Any other 402 is left alone.
  bool _isAccountBlocked(DioException err) {
    if (err.response?.statusCode != 402) return false;
    final data = err.response?.data;
    if (data is Map) {
      final error = data['error'];
      if (error is Map && error['code'] == 'account_blocked') return true;
    }
    return false;
  }

  Future<void> _expireSession(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    await SecureStorageService.clearAll();
    sessionExpiredNotifier.value = true;
    handler.reject(err);
  }
}

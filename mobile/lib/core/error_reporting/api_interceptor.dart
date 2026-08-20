import 'package:dio/dio.dart';
import 'breadcrumbs.dart';
import 'error_reporter.dart';

class ErrorReportingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.extra['__er_start'] = DateTime.now().millisecondsSinceEpoch;
    handler.next(options);
  }

  @override
  void onResponse(Response<dynamic> response, ResponseInterceptorHandler handler) {
    final start = response.requestOptions.extra['__er_start'] as int?;
    final duration = start != null
        ? DateTime.now().millisecondsSinceEpoch - start
        : null;
    BreadcrumbsTracker.addHttp(
      method: response.requestOptions.method,
      path: response.requestOptions.path,
      statusCode: response.statusCode,
      durationMs: duration,
    );
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final status = err.response?.statusCode;
    BreadcrumbsTracker.addHttp(
      method: err.requestOptions.method,
      path: err.requestOptions.path,
      statusCode: status,
    );

    if (shouldReport(err)) {
      ErrorReporter.report(
        err,
        err.stackTrace,
        severity: (status != null && status >= 500) ? 'ERROR' : 'WARNING',
        kind: _kind(err),
        requestPath: err.requestOptions.path,
        requestMethod: err.requestOptions.method,
        statusCode: status,
      );
    }

    handler.next(err);
  }

  bool shouldReport(DioException err) {
    final status = err.response?.statusCode;
    final path = err.requestOptions.path;
    if (status == 401) return false;
    if (status == 422) return false;
    if (path.contains('/api/error-report')) return false;
    if (path.contains('/api/auth/refresh')) return false;
    if (path.contains('/api/auth/login')) {
      if (status != null && status < 500) return false;
    }
    return true;
  }

  String _kind(DioException err) {
    switch (err.type) {
      case DioExceptionType.connectionError:
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.sendTimeout:
        return 'NETWORK';
      default:
        return 'EXCEPTION';
    }
  }
}

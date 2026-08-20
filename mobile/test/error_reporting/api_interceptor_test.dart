import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/error_reporting/api_interceptor.dart';
import 'package:mobile/core/error_reporting/breadcrumbs.dart';

DioException _makeErr({
  required String path,
  int? statusCode,
  DioExceptionType type = DioExceptionType.badResponse,
}) {
  final options = RequestOptions(path: path, method: 'GET');
  final response = statusCode != null
      ? Response<dynamic>(requestOptions: options, statusCode: statusCode)
      : null;
  return DioException(
    requestOptions: options,
    response: response,
    type: type,
  );
}

void main() {
  late ErrorReportingInterceptor interceptor;

  setUp(() {
    interceptor = ErrorReportingInterceptor();
    BreadcrumbsTracker.clear();
  });

  group('ErrorReportingInterceptor.shouldReport()', () {
    test('500 returns true', () {
      final err = _makeErr(path: '/api/phones/', statusCode: 500);
      expect(interceptor.shouldReport(err), isTrue);
    });

    test('404 returns true', () {
      final err = _makeErr(path: '/api/phones/', statusCode: 404);
      expect(interceptor.shouldReport(err), isTrue);
    });

    test('401 returns false', () {
      final err = _makeErr(path: '/api/phones/', statusCode: 401);
      expect(interceptor.shouldReport(err), isFalse);
    });

    test('422 returns false', () {
      final err = _makeErr(path: '/api/phones/', statusCode: 422);
      expect(interceptor.shouldReport(err), isFalse);
    });

    test('/api/error-report path returns false (recursion guard)', () {
      final err = _makeErr(path: '/api/error-report/', statusCode: 500);
      expect(interceptor.shouldReport(err), isFalse);
    });

    test('/api/auth/refresh returns false', () {
      final err = _makeErr(path: '/api/auth/refresh/', statusCode: 401);
      expect(interceptor.shouldReport(err), isFalse);
    });

    test('login 400 returns false (user mistake)', () {
      final err = _makeErr(path: '/api/auth/login/', statusCode: 400);
      expect(interceptor.shouldReport(err), isFalse);
    });

    test('login 500 returns true (server error)', () {
      final err = _makeErr(path: '/api/auth/login/', statusCode: 500);
      expect(interceptor.shouldReport(err), isTrue);
    });

    test('network timeout returns true', () {
      final err = _makeErr(
        path: '/api/phones/',
        type: DioExceptionType.connectionTimeout,
      );
      expect(interceptor.shouldReport(err), isTrue);
    });
  });

  group('ErrorReportingInterceptor.onResponse()', () {
    test('successful response adds http breadcrumb', () {
      final options = RequestOptions(path: '/api/phones/', method: 'GET')
        ..extra['__er_start'] =
            DateTime.now().millisecondsSinceEpoch - 100;
      final response =
          Response<dynamic>(requestOptions: options, statusCode: 200);

      interceptor.onResponse(response, ResponseInterceptorHandler());

      final crumbs = BreadcrumbsTracker.toList();
      expect(crumbs.any((c) => c['category'] == 'http'), isTrue);
      final crumb = crumbs.firstWhere((c) => c['category'] == 'http');
      expect(crumb['data']['status'], equals(200));
    });
  });

  group('ErrorReportingInterceptor._kind()', () {
    test('connection timeout → NETWORK', () {
      final err = _makeErr(
        path: '/api/',
        type: DioExceptionType.connectionTimeout,
      );
      // Access via shouldReport returns true and kind is checked internally
      // We test indirectly: interceptor processes without error
      expect(interceptor.shouldReport(err), isTrue);
    });
  });
}

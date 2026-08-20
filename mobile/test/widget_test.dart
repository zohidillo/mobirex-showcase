import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/app.dart';
import 'package:mobile/core/network/dio_client.dart';
import 'package:mobile/core/network/dio_providers.dart';

// Immediately rejects all requests so no real HTTP is made in widget tests.
class _MockDioClient extends DioClient {
  _MockDioClient() {
    dio = Dio(BaseOptions(baseUrl: 'https://localhost'));
    dio.interceptors.add(_ImmediateRejectInterceptor());
  }
}

class _ImmediateRejectInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    handler.reject(
      DioException(
        requestOptions: options,
        type: DioExceptionType.connectionError,
      ),
    );
  }
}

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          dioClientProvider.overrideWith((_) => _MockDioClient()),
        ],
        child: const VelmoraApp(),
      ),
    );
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}

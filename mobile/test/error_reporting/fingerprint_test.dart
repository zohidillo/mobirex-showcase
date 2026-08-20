import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/error_reporting/fingerprint.dart';

void main() {
  group('computeFingerprint', () {
    test('same input produces same hash', () {
      final a = computeFingerprint(
        errorType: 'TypeError',
        requestPath: '/api/phones/',
        statusCode: 500,
      );
      final b = computeFingerprint(
        errorType: 'TypeError',
        requestPath: '/api/phones/',
        statusCode: 500,
      );
      expect(a, equals(b));
    });

    test('different path produces different hash', () {
      final a = computeFingerprint(
        errorType: 'TypeError',
        requestPath: '/api/phones/',
        statusCode: 500,
      );
      final b = computeFingerprint(
        errorType: 'TypeError',
        requestPath: '/api/accessories/',
        statusCode: 500,
      );
      expect(a, isNot(equals(b)));
    });

    test('different status produces different hash', () {
      final a = computeFingerprint(
        errorType: 'TypeError',
        requestPath: '/api/phones/',
        statusCode: 500,
      );
      final b = computeFingerprint(
        errorType: 'TypeError',
        requestPath: '/api/phones/',
        statusCode: 404,
      );
      expect(a, isNot(equals(b)));
    });

    test('null optional fields produce stable hash', () {
      final a = computeFingerprint(errorType: 'DioException');
      final b = computeFingerprint(errorType: 'DioException');
      expect(a, equals(b));
      expect(a.length, equals(16));
    });
  });
}

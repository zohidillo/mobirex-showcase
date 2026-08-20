import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:mobile/core/error_reporting/error_queue.dart';
import 'package:mobile/core/error_reporting/models/error_event.dart';

ErrorEvent _makeEvent({String fingerprint = 'fp_test', String errorType = 'TypeError'}) =>
    ErrorEvent(
      severity: 'ERROR',
      kind: 'EXCEPTION',
      errorType: errorType,
      errorMessage: 'test error',
      appVersion: '1.0.0+1',
      platform: 'android',
      context: const {},
      occurredAt: DateTime(2025, 1, 1, 12, 0, 0),
      fingerprint: fingerprint,
    );

void main() {
  setUp(() async {
    SharedPreferences.setMockInitialValues({});
  });

  group('ErrorQueue', () {
    test('enqueue and drain returns the event', () async {
      final event = _makeEvent();
      await ErrorQueue.enqueue(event);
      final drained = await ErrorQueue.drain();
      expect(drained.length, equals(1));
      expect(drained.first.fingerprint, equals('fp_test'));
      expect(drained.first.errorType, equals('TypeError'));
    });

    test('remove deletes matching event by fingerprint+occurredAt', () async {
      final event = _makeEvent();
      await ErrorQueue.enqueue(event);
      await ErrorQueue.remove(event);
      final drained = await ErrorQueue.drain();
      expect(drained, isEmpty);
    });

    test('size returns correct count', () async {
      await ErrorQueue.enqueue(_makeEvent(fingerprint: 'fp_1'));
      await ErrorQueue.enqueue(_makeEvent(fingerprint: 'fp_2'));
      expect(await ErrorQueue.size(), equals(2));
    });

    test('maxQueueSize is respected — oldest entry evicted', () async {
      for (var i = 0; i < ErrorQueue.maxQueueSize + 5; i++) {
        await ErrorQueue.enqueue(_makeEvent(fingerprint: 'fp_$i'));
      }
      expect(await ErrorQueue.size(), equals(ErrorQueue.maxQueueSize));
    });

    test('corrupt entry is skipped on drain', () async {
      SharedPreferences.setMockInitialValues({
        'mobirex_error_queue_v1': ['not-valid-json', '{}'],
      });
      final drained = await ErrorQueue.drain();
      expect(drained, isEmpty);
    });
  });
}

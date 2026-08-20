import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/error_reporting/breadcrumbs.dart';

void main() {
  setUp(() => BreadcrumbsTracker.clear());

  group('BreadcrumbsTracker', () {
    test('adds navigation breadcrumb', () {
      BreadcrumbsTracker.addNavigation(from: '/login', to: '/dashboard');
      final list = BreadcrumbsTracker.toList();
      expect(list.length, equals(1));
      expect(list.first['category'], equals('navigation'));
      expect(list.first['message'], contains('/dashboard'));
    });

    test('adds http breadcrumb with status and duration', () {
      BreadcrumbsTracker.addHttp(
        method: 'POST',
        path: '/api/phones/',
        statusCode: 201,
        durationMs: 120,
      );
      final list = BreadcrumbsTracker.toList();
      expect(list.first['category'], equals('http'));
      expect(list.first['data']['status'], equals(201));
      expect(list.first['data']['duration_ms'], equals(120));
    });

    test('adds ui and log breadcrumbs', () {
      BreadcrumbsTracker.addUi('button_tap', {'button': 'submit'});
      BreadcrumbsTracker.addLog('user action');
      final list = BreadcrumbsTracker.toList();
      expect(list[0]['category'], equals('ui'));
      expect(list[1]['category'], equals('log'));
    });

    test('oldest entry is removed when maxSize exceeded', () {
      for (var i = 0; i < 22; i++) {
        BreadcrumbsTracker.addLog('entry $i');
      }
      final list = BreadcrumbsTracker.toList();
      expect(list.length, equals(BreadcrumbsTracker.maxSize));
      // First two entries (0, 1) should be gone
      expect(list.first['message'], equals('entry 2'));
    });

    test('clear empties buffer', () {
      BreadcrumbsTracker.addLog('something');
      BreadcrumbsTracker.clear();
      expect(BreadcrumbsTracker.toList(), isEmpty);
    });
  });
}

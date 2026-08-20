import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/dio_client.dart';
import 'package:mobile/core/network/dio_providers.dart';
import 'package:mobile/features/debt/presentation/providers/debt_provider.dart';
import 'package:mobile/features/expenses/presentation/providers/expense_provider.dart';
import 'package:mobile/features/phones/presentation/providers/phone_provider.dart';

// ---------------------------------------------------------------------------
// Platform channel mocks — prevent MissingPluginException in tests
// ---------------------------------------------------------------------------

void _mockPlatformChannels() {
  // SecureStorage
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(
    const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
    (_) async => null,
  );
  // DeviceInfo
  for (final ch in [
    'plugins.flutter.io/device_info',
    'dev.fluttercommunity.plus/device_info',
  ]) {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
      MethodChannel(ch),
      (_) async => <String, dynamic>{},
    );
  }
  // PackageInfo
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(
    const MethodChannel('dev.fluttercommunity.plus/package_info'),
    (_) async => {
      'appName': 'test',
      'packageName': 'com.test',
      'version': '1.0.0',
      'buildNumber': '1',
      'buildSignature': '',
      'installerStore': '',
    },
  );
  // Connectivity
  TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
      .setMockMethodCallHandler(
    const MethodChannel('dev.fluttercommunity.plus/connectivity'),
    (_) async => ['wifi'],
  );
}

/// Creates a DioClient that rejects every request immediately (no server needed).
/// Inserts the reject interceptor at index 0 so it runs before all others.
DioClient _createRejectingClient() {
  final client = DioClient();
  client.dio.interceptors.insert(
    0,
    InterceptorsWrapper(
      onRequest: (options, handler) => handler.reject(
        DioException(
          requestOptions: options,
          type: DioExceptionType.connectionError,
        ),
      ),
    ),
  );
  return client;
}

/// Waits until the given [condition] is satisfied, polling every microtask.
/// Throws if [timeout] is exceeded.
Future<void> _until(
  bool Function() condition, {
  Duration timeout = const Duration(seconds: 3),
}) async {
  final deadline = DateTime.now().add(timeout);
  while (!condition()) {
    if (DateTime.now().isAfter(deadline)) {
      throw TimeoutException('Condition not met within $timeout');
    }
    await Future<void>.delayed(const Duration(milliseconds: 5));
  }
}

// ---------------------------------------------------------------------------
// Bug 1 — validator lambdas (mirrors add_phone_page.dart exactly)
// ---------------------------------------------------------------------------

String? _storageValidator(String? v) =>
    v == null ? 'Xotira hajmini tanlang' : null;

String? _imeiValidator(String? v) =>
    v == null || v.trim().isEmpty ? 'IMEI kiritish shart' : null;

String? _fromByValidator(String? v) =>
    v == null || v.trim().isEmpty ? 'Qayerdan olinganini kiriting' : null;

Widget _buildValidatorForm({
  String? Function(String?)? storageValidator,
  String? Function(String?)? imeiValidator,
  String? Function(String?)? fromByValidator,
}) {
  final key = GlobalKey<FormState>();
  return MaterialApp(
    home: Scaffold(
      body: Form(
        key: key,
        child: Column(
          children: [
            DropdownButtonFormField<String?>(
              items: const [
                DropdownMenuItem(value: '128', child: Text('128 GB')),
              ],
              onChanged: (_) {},
              validator: storageValidator,
            ),
            TextFormField(key: const Key('imei'), validator: imeiValidator),
            TextFormField(
                key: const Key('from_by'), validator: fromByValidator),
            ElevatedButton(
              key: const Key('submit'),
              onPressed: () => key.currentState!.validate(),
              child: const Text('Submit'),
            ),
          ],
        ),
      ),
    ),
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

void main() {
  // -------------------------------------------------------------------------
  // Bug 1 — form validator tests (no HTTP needed)
  // -------------------------------------------------------------------------
  group('Bug 1 — AddPhonePage form validators', () {
    testWidgets('storage null → shows required validation error',
        (tester) async {
      await tester.pumpWidget(
          _buildValidatorForm(storageValidator: _storageValidator));
      await tester.tap(find.byKey(const Key('submit')));
      await tester.pump();
      expect(find.text('Xotira hajmini tanlang'), findsOneWidget);
    });

    testWidgets('imei empty → shows required validation error',
        (tester) async {
      await tester.pumpWidget(
          _buildValidatorForm(imeiValidator: _imeiValidator));
      await tester.tap(find.byKey(const Key('submit')));
      await tester.pump();
      expect(find.text('IMEI kiritish shart'), findsOneWidget);
    });

    testWidgets('from_by empty → shows required validation error',
        (tester) async {
      await tester.pumpWidget(
          _buildValidatorForm(fromByValidator: _fromByValidator));
      await tester.tap(find.byKey(const Key('submit')));
      await tester.pump();
      expect(find.text('Qayerdan olinganini kiriting'), findsOneWidget);
    });

    testWidgets('all fields filled → no validation errors', (tester) async {
      await tester.pumpWidget(
        _buildValidatorForm(
          storageValidator: _storageValidator,
          imeiValidator: _imeiValidator,
          fromByValidator: _fromByValidator,
        ),
      );

      await tester.tap(find.byType(DropdownButtonFormField<String?>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('128 GB').last);
      await tester.pumpAndSettle();

      await tester.enterText(
          find.byKey(const Key('imei')), '123456789012345');
      await tester.enterText(
          find.byKey(const Key('from_by')), 'Distributor');

      await tester.tap(find.byKey(const Key('submit')));
      await tester.pump();

      expect(find.text('Xotira hajmini tanlang'), findsNothing);
      expect(find.text('IMEI kiritish shart'), findsNothing);
      expect(find.text('Qayerdan olinganini kiriting'), findsNothing);
    });
  });

  // -------------------------------------------------------------------------
  // Bug 2 — provider invalidation tests
  // -------------------------------------------------------------------------
  group('Bug 2 — provider invalidation on auth transitions', () {
    setUpAll(() {
      TestWidgetsFlutterBinding.ensureInitialized();
      _mockPlatformChannels();
    });

    /// Waits for the provider's load() to finish (isLoading → false),
    /// then invalidates and returns the fresh state.
    Future<T> _invalidateAndGetFresh<N extends StateNotifier<T>, T>(
      ProviderContainer container,
      StateNotifierProvider<N, T> provider,
      bool Function(T) isLoading,
    ) async {
      // Wait for the initial load to complete (success or failure).
      await _until(() => !isLoading(container.read(provider)));
      // Simulate _invalidateAllUserData()
      container.invalidate(provider);
      // Re-reading creates a fresh notifier — return its initial state.
      return container.read(provider);
    }

    test('unpaidDebtsProvider: invalidation creates fresh initial state',
        () async {
      final container = ProviderContainer(overrides: [
        dioClientProvider.overrideWithValue(_createRejectingClient()),
      ]);

      container.read(unpaidDebtsProvider); // triggers load()

      final fresh = await _invalidateAndGetFresh(
        container,
        unpaidDebtsProvider,
        (s) => s.isLoading,
      );

      expect(fresh.isLoading, isTrue); // new notifier started loading
      expect(fresh.items, isEmpty); // clean slate
      expect(fresh.error, isNull); // no prior error

      // Let the new notifier's load() complete before disposing.
      await _until(
          () => !container.read(unpaidDebtsProvider).isLoading);
      container.dispose();
    });

    test('expensesProvider: invalidation creates fresh initial state',
        () async {
      final container = ProviderContainer(overrides: [
        dioClientProvider.overrideWithValue(_createRejectingClient()),
      ]);

      container.read(expensesProvider);

      final fresh = await _invalidateAndGetFresh(
        container,
        expensesProvider,
        (s) => s.isLoading,
      );

      expect(fresh.isLoading, isTrue);
      expect(fresh.items, isEmpty);
      expect(fresh.error, isNull);

      await _until(() => !container.read(expensesProvider).isLoading);
      container.dispose();
    });

    test('unsoldPhonesProvider: invalidation creates fresh initial state',
        () async {
      final container = ProviderContainer(overrides: [
        dioClientProvider.overrideWithValue(_createRejectingClient()),
      ]);

      container.read(unsoldPhonesProvider);

      final fresh = await _invalidateAndGetFresh(
        container,
        unsoldPhonesProvider,
        (s) => s.isLoading,
      );

      expect(fresh.isLoading, isTrue);
      expect(fresh.phones, isEmpty);
      expect(fresh.error, isNull);

      await _until(() => !container.read(unsoldPhonesProvider).isLoading);
      container.dispose();
    });

    test('two sequential invalidations simulate logout → login for new user',
        () async {
      final container = ProviderContainer(overrides: [
        dioClientProvider.overrideWithValue(_createRejectingClient()),
      ]);

      // ---- User A: provider initialised, load() fails ----
      container.read(unpaidDebtsProvider);
      await _until(() => !container.read(unpaidDebtsProvider).isLoading);
      expect(container.read(unpaidDebtsProvider).isLoading, isFalse);

      // ---- Logout: _invalidateAllUserData() ----
      container.invalidate(unpaidDebtsProvider);
      final afterLogout = container.read(unpaidDebtsProvider);
      expect(afterLogout.isLoading, isTrue); // fresh notifier started
      expect(afterLogout.error, isNull);

      // Let the new load() complete before the next invalidation.
      await _until(() => !container.read(unpaidDebtsProvider).isLoading);

      // ---- Login User B: _invalidateAllUserData() again ----
      container.invalidate(unpaidDebtsProvider);
      final afterLogin = container.read(unpaidDebtsProvider);
      expect(afterLogin.isLoading, isTrue); // another fresh start
      expect(afterLogin.items, isEmpty); // no stale data from User A
      expect(afterLogin.error, isNull);

      await _until(() => !container.read(unpaidDebtsProvider).isLoading);
      container.dispose();
    });
  });
}

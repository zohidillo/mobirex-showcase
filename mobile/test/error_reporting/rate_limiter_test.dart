import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/error_reporting/rate_limiter.dart';

void main() {
  setUp(() => RateLimiter.reset());

  group('RateLimiter', () {
    test('first send is allowed', () {
      expect(RateLimiter.shouldSend('fp_abc'), isTrue);
    });

    test('same fingerprint within 5 minutes is blocked after first send', () {
      RateLimiter.recordSent('fp_abc');
      expect(RateLimiter.shouldSend('fp_abc'), isFalse);
    });

    test('different fingerprints are independent', () {
      RateLimiter.recordSent('fp_abc');
      expect(RateLimiter.shouldSend('fp_xyz'), isTrue);
    });

    test('global bucket blocks after 5 sends in same minute', () {
      for (var i = 0; i < 5; i++) {
        expect(RateLimiter.shouldSend('fp_$i'), isTrue);
        RateLimiter.recordSent('fp_$i');
      }
      // 6th event — different fingerprint, but global limit hit
      expect(RateLimiter.shouldSend('fp_new'), isFalse);
    });

    test('reset clears all state', () {
      RateLimiter.recordSent('fp_abc');
      RateLimiter.reset();
      expect(RateLimiter.shouldSend('fp_abc'), isTrue);
    });
  });
}

import 'package:flutter/foundation.dart';

// Fired by AuthInterceptor when refresh fails; AuthNotifier listens and
// transitions to unauthenticated without a circular provider dependency.
final sessionExpiredNotifier = ValueNotifier<bool>(false);

// Fired by AuthInterceptor when a business request returns 402
// (code == "account_blocked"). This is billing, NOT a token problem:
// there is no refresh and no logout — AuthNotifier only refreshes /api/me/
// so the router can send the user to the blocked screen.
final accountBlockedNotifier = ValueNotifier<bool>(false);

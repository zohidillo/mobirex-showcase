import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/profile/data/models/user_model.dart';

class RouterNotifier extends ChangeNotifier {
  final Ref _ref;

  RouterNotifier(this._ref) {
    _ref.listen(authProvider, (previous, next) => notifyListeners());
  }

  String? redirect(BuildContext context, GoRouterState state) {
    final auth = _ref.read(authProvider);
    final loc = state.matchedLocation;

    switch (auth.status) {
      case AuthStatus.loading:
        return loc == '/splash' ? null : '/splash';
      case AuthStatus.unauthenticated:
        // /contact — ro'yxatdan o'tmagan odam uchun, login bilan bir qatorda.
        return (loc == '/login' || loc == '/contact') ? null : '/login';
      case AuthStatus.pinRequired:
        if (loc == '/pin/verify') return null;
        return '/pin/verify';
      case AuthStatus.authenticated:
        // Billing block wins over normal navigation. Covers BOTH entry paths:
        // (a) a mid-session 402 refreshes /api/me/ and flips billing.isBlocked;
        // (b) /api/me/ on app open already reports isBlocked. VIP is exempt
        // (isBillingBlockedProvider checks !isVip). No auto-logout here.
        final blocked = _ref.read(isBillingBlockedProvider);
        if (blocked) {
          return loc == '/blocked' ? null : '/blocked';
        }
        if (loc == '/login' ||
            loc == '/splash' ||
            loc == '/pin/verify' ||
            loc == '/blocked') {
          return _homeFor(auth.user);
        }
        return null;
    }
  }

  String _homeFor(UserModel? user) {
    if (user != null && user.isOwner) return '/dashboard';
    if (user != null && user.isAccessorySeller && !user.isPhoneSeller) {
      return '/accessories/unsold';
    }
    return '/phones/unsold';
  }
}

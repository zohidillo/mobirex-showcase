import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/error_reporting/error_reporter.dart';
import '../../../../core/network/dio_providers.dart';
import '../../../../core/network/session_notifier.dart';
import '../../../../core/theme/theme_provider.dart';
import '../../../../core/utils/safe_debug_log.dart';
import '../../../../shared/providers/category_provider.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../accessories/presentation/providers/accessory_provider.dart';
import '../../../auth/data/models/login_request.dart';
import '../../../auth/data/repositories/auth_repository.dart';
import '../../../capital/presentation/providers/capital_provider.dart';
import '../../../dashboard/presentation/providers/dashboard_provider.dart';
import '../../../debt/presentation/providers/debt_provider.dart';
import '../../../expenses/presentation/providers/expense_provider.dart';
import '../../../extra_profit/presentation/providers/extra_profit_provider.dart';
import '../../../phones/presentation/providers/phone_provider.dart';
import '../../../profile/data/models/user_model.dart';
import '../../../salaries/presentation/providers/salary_provider.dart';
import '../../../support/presentation/providers/support_provider.dart';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

enum AuthStatus { loading, unauthenticated, pinRequired, authenticated }

class AuthState {
  final AuthStatus status;
  final UserModel? user;
  final String? error;

  /// Machine-readable error code for the last auth failure, when the server
  /// provided one. Currently only "account_blocked" is used, so the login
  /// page can distinguish a billing block from a wrong password.
  final String? errorCode;

  const AuthState({
    required this.status,
    this.user,
    this.error,
    this.errorCode,
  });

  const AuthState.loading()
    : status = AuthStatus.loading,
      user = null,
      error = null,
      errorCode = null;

  const AuthState.unauthenticated()
    : status = AuthStatus.unauthenticated,
      user = null,
      error = null,
      errorCode = null;

  AuthState copyWith({
    AuthStatus? status,
    UserModel? user,
    String? error,
    String? errorCode,
    bool clearError = false,
  }) => AuthState(
    status: status ?? this.status,
    user: user ?? this.user,
    error: clearError ? null : (error ?? this.error),
    errorCode: clearError ? null : (errorCode ?? this.errorCode),
  );
}

// ---------------------------------------------------------------------------
// Providers
// ---------------------------------------------------------------------------

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.read(dioClientProvider));
});

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref);
});

/// Real-time billing state of the signed-in user (null when logged out).
/// Derived from `/api/me/` — the source of truth for the billing UI.
final billingStatusProvider = Provider<BillingStatus?>((ref) {
  return ref.watch(authProvider).user?.billing;
});

/// Whether the amber grace banner should be shown (grace + not VIP).
final showGraceBannerProvider = Provider<bool>((ref) {
  return ref.watch(authProvider).user?.showGraceBanner ?? false;
});

/// Whether the signed-in user is billing-blocked (blocked + not VIP).
final isBillingBlockedProvider = Provider<bool>((ref) {
  return ref.watch(authProvider).user?.isBillingBlocked ?? false;
});

// ---------------------------------------------------------------------------
// Notifier
// ---------------------------------------------------------------------------

class AuthNotifier extends StateNotifier<AuthState> {
  final Ref _ref;

  AuthNotifier(this._ref) : super(const AuthState.loading()) {
    sessionExpiredNotifier.addListener(_onSessionExpired);
    accountBlockedNotifier.addListener(_onAccountBlocked);
    initialize();
  }

  AuthRepository get _repo => _ref.read(authRepositoryProvider);

  @override
  void dispose() {
    sessionExpiredNotifier.removeListener(_onSessionExpired);
    accountBlockedNotifier.removeListener(_onAccountBlocked);
    super.dispose();
  }

  void _onSessionExpired() {
    if (sessionExpiredNotifier.value) {
      sessionExpiredNotifier.value = false;
      _invalidateAllUserData();
      state = const AuthState.unauthenticated();
    }
  }

  /// Reacts to a 402 billing block raised by the interceptor. Deliberately
  /// does NOT log out: it only re-reads /api/me/ (which is exempt from the
  /// block and returns 200) so `billing.isBlocked` becomes true and the
  /// router redirects to the blocked screen. The user stays signed in.
  void _onAccountBlocked() {
    if (accountBlockedNotifier.value) {
      accountBlockedNotifier.value = false;
      _refreshBillingState();
    }
  }

  Future<void> _refreshBillingState() async {
    if (state.status != AuthStatus.authenticated &&
        state.status != AuthStatus.pinRequired) {
      return;
    }
    try {
      final user = await _repo.getMe();
      state = state.copyWith(user: user);
    } catch (_) {
      // A later /api/me/ call will reconcile the billing state.
    }
  }

  /// Invalidates all user-specific data providers so that the next
  /// authenticated user starts with a clean slate.
  /// Add new data providers here as the app grows.
  void _invalidateAllUserData() {
    _ref.invalidate(unpaidDebtsProvider);
    _ref.invalidate(closedDebtsProvider);
    _ref.invalidate(debtPaymentsProvider);
    _ref.invalidate(expensesProvider);
    _ref.invalidate(extraProfitsProvider);
    _ref.invalidate(salariesProvider);
    _ref.invalidate(staffListProvider);
    _ref.invalidate(unsoldAccessoriesProvider);
    _ref.invalidate(soldAccessoriesProvider);
    _ref.invalidate(accessoryCapitalProvider);
    _ref.invalidate(phoneCapitalProvider);
    _ref.invalidate(unsoldPhonesProvider);
    _ref.invalidate(soldPhonesProvider);
    _ref.invalidate(dashboardProvider);
    _ref.invalidate(supportListProvider);
    _ref.invalidate(supportDetailProvider);
    _ref.invalidate(phoneCategoriesProvider);
    _ref.invalidate(accessoryCategoriesProvider);
  }

  Future<void> initialize() async {
    try {
      final user = await _repo.getMe();
      await _ref.read(themeModeProvider.notifier).setFromServer(user.theme);
      ErrorReporter.setUser(
        id: user.id,
        username: user.username,
        roles: user.roles.map((r) => r.role).toList(),
        branches: user.branches.map((b) => b.name).toList(),
      );
      if (user.hasPin) {
        state = AuthState(status: AuthStatus.pinRequired, user: user);
      } else {
        state = AuthState(status: AuthStatus.authenticated, user: user);
      }
    } catch (_) {
      state = const AuthState.unauthenticated();
    }
  }

  Future<void> login(String username, String password) async {
    state = state.copyWith(clearError: true);
    try {
      await _repo.login(LoginRequest(username: username, password: password));
      safeAuthLog('Login succeeded; calling /api/me/ after login.');

      late final UserModel user;
      try {
        user = await _repo.getMe();
      } catch (error) {
        safeAuthLog('/api/me/ failed after successful login.');
        state = AuthState(
          status: AuthStatus.unauthenticated,
          error: parsePostLoginProfileError(error),
        );
        return;
      }

      _invalidateAllUserData();

      await _ref.read(themeModeProvider.notifier).setFromServer(user.theme);
      ErrorReporter.setUser(
        id: user.id,
        username: user.username,
        roles: user.roles.map((r) => r.role).toList(),
        branches: user.branches.map((b) => b.name).toList(),
      );
      if (user.hasPin) {
        state = AuthState(status: AuthStatus.pinRequired, user: user);
      } else {
        state = AuthState(status: AuthStatus.authenticated, user: user);
      }
    } catch (e) {
      state = AuthState(
        status: AuthStatus.unauthenticated,
        error: parseLoginError(e),
        errorCode: isAccountBlockedError(e) ? 'account_blocked' : null,
      );
    }
  }

  Future<bool> verifyPin(String pin) async {
    try {
      await _repo.verifyPin(pin);
      state = state.copyWith(status: AuthStatus.authenticated);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> setPin(String pin) async {
    try {
      final result = await _repo.setPin(pin);
      if (result.success) {
        final updatedUser = state.user?.copyWith(
          hasPin: result.hasPin ?? true,
          pinEnabled: result.pinEnabled ?? true,
        );
        state = state.copyWith(
          user: updatedUser,
          status: AuthStatus.authenticated,
        );
        return true;
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<bool> changePin(String oldPin, String newPin) async {
    try {
      await _repo.changePin(oldPin, newPin);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> updateUser(UserModel user) async {
    await _ref.read(themeModeProvider.notifier).setFromServer(user.theme);
    state = state.copyWith(user: user);
  }

  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
    required String newPasswordConfirm,
  }) async {
    await _repo.changePassword(
      oldPassword: oldPassword,
      newPassword: newPassword,
      newPasswordConfirm: newPasswordConfirm,
    );
  }

  Future<void> logout() async {
    await _repo.logout();
    ErrorReporter.clearUser();
    _invalidateAllUserData();
    state = const AuthState.unauthenticated();
  }

  /// Permanently deletes the account on the backend, then runs the normal
  /// logout flow so local tokens are cleared and the user lands on login.
  /// On failure the local session is left untouched and the error is rethrown
  /// for the UI to surface.
  Future<void> deleteAccount() async {
    await _repo.deleteAccount();
    await logout();
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../error_reporting/navigation_observer.dart';
import '../router/router_notifier.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/auth/presentation/pages/pin_verify_page.dart';
import '../../features/auth/presentation/pages/pin_setup_page.dart';
import '../../features/auth/presentation/pages/blocked_page.dart';
import '../../features/auth/presentation/pages/contact_request_page.dart';
import '../../features/auth/presentation/pages/pin_change_page.dart';
import '../../features/profile/presentation/pages/profile_page.dart';
import '../../features/phones/presentation/pages/unsold_phones_page.dart';
import '../../features/phones/presentation/pages/sold_phones_page.dart';
import '../../features/phones/presentation/pages/add_phone_page.dart';
import '../../features/accessories/presentation/pages/unsold_accessories_page.dart';
import '../../features/accessories/presentation/pages/sold_accessories_page.dart';
import '../../features/accessories/presentation/pages/add_accessory_page.dart';
import '../../features/debt/presentation/pages/unpaid_debts_page.dart';
import '../../features/debt/presentation/pages/closed_debts_page.dart';
import '../../features/expenses/presentation/pages/expenses_page.dart';
import '../../features/salaries/presentation/pages/salaries_page.dart';
import '../../features/extra_profit/presentation/pages/extra_profit_page.dart';
import '../../features/capital/presentation/pages/phone_capital_page.dart';
import '../../features/capital/presentation/pages/accessory_capital_page.dart';
import '../../features/dashboard/presentation/pages/dashboard_entry_page.dart';
import '../../features/dashboard/presentation/pages/owner_staff_list_page.dart';
import '../../features/dashboard/presentation/pages/staff_dashboard_page.dart';
import '../../features/support/presentation/pages/account_delete_request_page.dart';
import '../../features/support/presentation/pages/support_page.dart';
import '../../features/support/presentation/pages/support_request_detail_page.dart';
import '../../shared/widgets/app_shell.dart';
import '../../shared/widgets/mobirex_logo.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final notifier = RouterNotifier(ref);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: notifier,
    redirect: notifier.redirect,
    observers: [BreadcrumbNavigatorObserver()],
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const _SplashPage(),
      ),
      GoRoute(path: '/login', builder: (context, state) => const LoginPage()),
      // AppShell'dan tashqarida — drawer va grace banner yo'q. Faqat login
      // ekranidan ochiladi (ro'yxatdan o'tmagan foydalanuvchi uchun).
      GoRoute(
        path: '/contact',
        builder: (context, state) => const ContactRequestPage(),
      ),
      GoRoute(
        path: '/blocked',
        builder: (context, state) => const BlockedPage(),
      ),
      GoRoute(
        path: '/pin/verify',
        builder: (context, state) => const PinVerifyPage(),
      ),
      GoRoute(
        path: '/pin/setup',
        builder: (context, state) => const PinSetupPage(),
      ),
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          // Dashboard
          GoRoute(
            path: '/dashboard',
            builder: (context, state) => const DashboardEntryPage(),
          ),
          GoRoute(
            path: '/dashboard/branch/:branchId/staff',
            builder: (context, state) {
              final branchId =
                  int.tryParse(state.pathParameters['branchId'] ?? '') ?? 0;
              final branchName = state.uri.queryParameters['branchName'] ?? '';
              return OwnerStaffListPage(
                branchId: branchId,
                branchName: branchName,
              );
            },
          ),
          GoRoute(
            path: '/dashboard/staff',
            builder: (context, state) {
              final p = state.uri.queryParameters;
              return StaffDashboardPage(
                branchId: int.tryParse(p['branchId'] ?? '') ?? 0,
                staffId: p['staffId'] != null
                    ? int.tryParse(p['staffId']!)
                    : null,
                role: p['role'] ?? 'PHONE_SELLER',
                branchName: p['branchName'] ?? '',
                staffName: p['staffName'],
              );
            },
          ),
          // Phones
          GoRoute(
            path: '/phones/unsold',
            builder: (context, state) => const UnsoldPhonesPage(),
          ),
          GoRoute(
            path: '/phones/sold',
            builder: (context, state) => const SoldPhonesPage(),
          ),
          GoRoute(
            path: '/phones/add',
            builder: (context, state) => const AddPhonePage(),
          ),
          // Accessories
          GoRoute(
            path: '/accessories/unsold',
            builder: (context, state) => const UnsoldAccessoriesPage(),
          ),
          GoRoute(
            path: '/accessories/sold',
            builder: (context, state) => const SoldAccessoriesPage(),
          ),
          GoRoute(
            path: '/accessories/add',
            builder: (context, state) => const AddAccessoryPage(),
          ),
          // Profile & PIN
          GoRoute(
            path: '/profile',
            builder: (context, state) => const ProfilePage(),
          ),
          GoRoute(
            path: '/pin/change',
            builder: (context, state) => const PinChangePage(),
          ),
          // Debts
          GoRoute(
            path: '/debts/unpaid',
            builder: (context, state) => const UnpaidDebtsPage(),
          ),
          GoRoute(
            path: '/debts/closed',
            builder: (context, state) => const ClosedDebtsPage(),
          ),
          // Expenses
          GoRoute(
            path: '/expenses',
            builder: (context, state) => const ExpensesPage(),
          ),
          // Salaries
          GoRoute(
            path: '/salaries',
            builder: (context, state) => const SalariesPage(),
          ),
          // Extra Profit
          GoRoute(
            path: '/extra-profits',
            builder: (context, state) => const ExtraProfitPage(),
          ),
          // Capital
          GoRoute(
            path: '/capital/phone',
            builder: (context, state) => const PhoneCapitalPage(),
          ),
          GoRoute(
            path: '/capital/accessory',
            builder: (context, state) => const AccessoryCapitalPage(),
          ),
          // Support
          GoRoute(
            path: '/support',
            builder: (context, state) => const SupportPage(),
          ),
          GoRoute(
            path: '/support/detail/:id',
            builder: (context, state) {
              final id = int.tryParse(state.pathParameters['id'] ?? '') ?? 0;
              return SupportRequestDetailPage(requestId: id);
            },
          ),
          GoRoute(
            path: '/account-delete',
            builder: (context, state) => const AccountDeleteRequestPage(),
          ),
        ],
      ),
    ],
  );
});

class _SplashPage extends ConsumerWidget {
  const _SplashPage();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            MobirexLogo(size: 96, showText: true),
            SizedBox(height: 24),
            CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../features/auth/presentation/providers/auth_provider.dart';
import 'owner_branch_list_page.dart';
import 'seller_dashboard_content.dart';

/// Kirish nuqtasi — `redesign4/dashboard/dashboard-entry.html`.
///
/// Marshrutlash mantig'i o'zgarmadi; faqat yuklanish ko'rinishi yangilandi.
class DashboardEntryPage extends ConsumerWidget {
  const DashboardEntryPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;

    if (user == null) {
      return const Scaffold(
        body: Center(
          child: SizedBox(
            width: 42,
            height: 42,
            child: CircularProgressIndicator(strokeWidth: 3.5),
          ),
        ),
      );
    }

    if (user.isOwner) {
      return const OwnerBranchListPage();
    }

    return SellerDashboardContent(user: user);
  }
}

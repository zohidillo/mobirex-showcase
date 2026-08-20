import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../features/auth/presentation/providers/auth_provider.dart';
import '../../../../features/profile/data/models/user_model.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';

/// Filiallar ro'yxati — `redesign4/dashboard/owner-branch-list.html`.
///
/// ⚠️ DEFEKT TUZATILDI: avval bu ekranda yuklanish va xato holatlari yo'q edi.
/// Ikkalasi ham MAVJUD `authProvider` holatidan olinadi
/// (`AuthStatus.loading`, `state.error`), yangi state o'ylab topilmadi;
/// qayta urinish ham mavjud `initialize()` metodini chaqiradi.
class OwnerBranchListPage extends ConsumerWidget {
  const OwnerBranchListPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final user = auth.user;
    final branches = user?.branches ?? [];

    return Scaffold(
      appBar: const VelmoraAppBar(subtitle: 'Dashboard', showDrawer: true),
      body: _buildBody(context, ref, auth, branches),
    );
  }

  Widget _buildBody(
    BuildContext context,
    WidgetRef ref,
    AuthState auth,
    List<UserBranch> branches,
  ) {
    if (auth.status == AuthStatus.loading && auth.user == null) {
      return const Center(
        child: SizedBox(
          width: 42,
          height: 42,
          child: CircularProgressIndicator(strokeWidth: 3.5),
        ),
      );
    }

    if (auth.error != null && auth.user == null) {
      return ErrorView(
        message: auth.error!,
        onRetry: () => ref.read(authProvider.notifier).initialize(),
      );
    }

    if (branches.isEmpty) {
      return const EmptyState(
        message: 'Filiallar topilmadi',
        icon: Icons.store_outlined,
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(
            AppSpacing.s4,
            AppSpacing.s4,
            AppSpacing.s4,
            10,
          ),
          child: Text('FILIALNI TANLANG', style: AppText.sectionLabel),
        ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.s4,
              0,
              AppSpacing.s4,
              AppSpacing.s6,
            ),
            itemCount: branches.length,
            separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.s3),
            itemBuilder: (context, i) => _BranchCard(
              branch: branches[i],
              onTap: () => _openStaffList(context, branches[i]),
            ),
          ),
        ),
      ],
    );
  }

  void _openStaffList(BuildContext context, UserBranch branch) {
    final uri = Uri(
      path: '/dashboard/branch/${branch.id}/staff',
      queryParameters: {'branchName': branch.name},
    );
    context.push(uri.toString());
  }
}

class _BranchCard extends StatelessWidget {
  final UserBranch branch;
  final VoidCallback onTap;

  const _BranchCard({required this.branch, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return AppCard(
      onTap: onTap,
      child: Row(
        children: [
          const Icon(Icons.store_outlined, color: AppColors.ink3, size: 22),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              branch.name,
              style: AppText.bodyLg,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const Icon(Icons.chevron_right, color: AppColors.ink3, size: 22),
        ],
      ),
    );
  }
}

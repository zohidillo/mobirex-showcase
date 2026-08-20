import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../features/salaries/data/models/staff_model.dart';
import '../providers/dashboard_provider.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_tag.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';

/// Xodimlar ro'yxati — `redesign4/dashboard/owner-staff-list.html`.
///
/// Yuklanish va xato holatlari mavjud `ownerStaffListProvider` ning
/// `AsyncValue` holatidan olinadi (yangi state qo'shilmadi).
class OwnerStaffListPage extends ConsumerWidget {
  final int branchId;
  final String branchName;

  const OwnerStaffListPage({
    super.key,
    required this.branchId,
    required this.branchName,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final staffAsync = ref.watch(ownerStaffListProvider(branchId));

    return Scaffold(
      appBar: VelmoraAppBar(subtitle: 'Xodimlar', caption: branchName),
      body: staffAsync.when(
        loading: () => const Center(
          child: SizedBox(
            width: 42,
            height: 42,
            child: CircularProgressIndicator(strokeWidth: 3.5),
          ),
        ),
        error: (e, _) => ErrorView(
          message: 'Xodimlarni yuklashda xato\n${parseApiError(e)}',
          onRetry: () => ref.invalidate(ownerStaffListProvider(branchId)),
        ),
        data: (staff) {
          if (staff.isEmpty) {
            return EmptyState(
              message: 'Xodimlar topilmadi',
              icon: Icons.people_outline,
              onRefresh: () => ref.invalidate(ownerStaffListProvider(branchId)),
            );
          }

          return ListView.separated(
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.s4,
              14,
              AppSpacing.s4,
              AppSpacing.s6,
            ),
            itemCount: staff.length,
            separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.s3),
            itemBuilder: (context, i) => _StaffCard(
              member: staff[i],
              onTap: () => _openDashboard(context, staff[i]),
            ),
          );
        },
      ),
    );
  }

  void _openDashboard(BuildContext context, StaffMember member) {
    final uri = Uri(
      path: '/dashboard/staff',
      queryParameters: {
        'branchId': '$branchId',
        'staffId': '${member.id}',
        'role': member.role,
        'branchName': branchName,
        'staffName': member.displayName,
      },
    );
    context.push(uri.toString());
  }
}

class _StaffCard extends StatelessWidget {
  final StaffMember member;
  final VoidCallback onTap;

  const _StaffCard({required this.member, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isPhone = member.role == 'PHONE_SELLER';
    final roleLabel = isPhone ? 'Telefon sotuvchi' : 'Aksessuar sotuvchi';

    return AppCard(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  member.displayName,
                  style: AppText.bodyLg,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 10),
              AppTag(
                label: roleLabel,
                color: isPhone ? AppColors.action : AppColors.ink2,
                size: AppTagSize.status,
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.only(top: 7),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    '@${member.username}',
                    style: AppText.meta,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const Icon(
                  Icons.chevron_right,
                  color: AppColors.ink3,
                  size: 20,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

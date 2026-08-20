import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/debt_provider.dart';
import '../widgets/debt_card.dart';
import '../widgets/debt_filter_bar.dart';
import '../widgets/debt_payment_history_sheet.dart';

class ClosedDebtsPage extends ConsumerStatefulWidget {
  const ClosedDebtsPage({super.key});

  @override
  ConsumerState<ClosedDebtsPage> createState() => _ClosedDebtsPageState();
}

class _ClosedDebtsPageState extends ConsumerState<ClosedDebtsPage> {
  final _searchCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  bool _showFilters = false;

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollCtrl.position.pixels >=
        _scrollCtrl.position.maxScrollExtent - 200) {
      ref.read(closedDebtsProvider.notifier).loadMore();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(closedDebtsProvider);
    final user = ref.watch(authProvider).user;
    final isOwner = user?.isOwner ?? false;

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'To\'langan qarzlar',
        showDrawer: true,
        actions: [
          AppHeaderButton(
            icon: Icons.list_alt_outlined,
            onPressed: () => context.go('/debts/unpaid'),
            tooltip: 'To\'lanmagan qarzlar',
          ),
        ],
        bottom: DebtFilterBar(
          searchCtrl: _searchCtrl,
          state: state,
          showBranch: isOwner,
          showDomain: isOwner,
          user: user,
          showFilters: _showFilters,
          onToggleFilters: () => setState(() => _showFilters = !_showFilters),
          onChanged: (f) =>
              ref.read(closedDebtsProvider.notifier).applyFilter(f),
        ),
      ),
      body: Column(
        children: [
          DebtFilterChips(
            filter: state.filter,
            user: user,
            onChanged: (f) =>
                ref.read(closedDebtsProvider.notifier).applyFilter(f),
          ),
          Expanded(child: _buildList(state)),
        ],
      ),
    );
  }

  Widget _buildList(DebtListState state) {
    if (state.isLoading) {
      return ListView.separated(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          AppSpacing.s4,
        ),
        itemCount: 5,
        separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.s3),
        itemBuilder: (_, _) => const AppCardSkeleton(),
      );
    }
    if (state.error != null && state.items.isEmpty) {
      return ErrorView(
        message: parseApiError(state.error),
        onRetry: () =>
            ref.read(closedDebtsProvider.notifier).load(refresh: true),
      );
    }
    if (state.items.isEmpty) {
      return EmptyState(
        message: 'Bu davrda yopilgan qarzlar yo\'q',
        icon: Icons.check_circle_outline,
        onRefresh: () =>
            ref.read(closedDebtsProvider.notifier).load(refresh: true),
      );
    }

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () =>
          ref.read(closedDebtsProvider.notifier).load(refresh: true),
      child: ListView.separated(
        controller: _scrollCtrl,
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          AppSpacing.s4,
        ),
        itemCount: state.items.length + (state.isLoadingMore ? 1 : 0),
        separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.s3),
        itemBuilder: (ctx, i) {
          if (i == state.items.length) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(14),
                child: SizedBox(
                  width: 28,
                  height: 28,
                  child: CircularProgressIndicator(strokeWidth: 3),
                ),
              ),
            );
          }
          final debt = state.items[i];
          return DebtCard(
            debt: debt,
            onTap: () => showModalBottomSheet(
              context: context,
              isScrollControlled: true,
              backgroundColor: AppColors.surface,
              barrierColor: AppColors.scrim,
              shape: const RoundedRectangleBorder(
                borderRadius: AppRadius.sheetRadius,
              ),
              builder: (_) => DebtPaymentHistorySheet(
                debt: debt,
                isOwner: ref.read(authProvider).user?.isOwner ?? false,
                canPay: false,
                canDelete: false,
                onPay: (_, {note}) async => null,
              ),
            ),
          );
        },
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_dialog.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/models/debt_model.dart';
import '../providers/debt_provider.dart';
import '../widgets/create_debt_sheet.dart';
import '../widgets/debt_card.dart';
import '../widgets/debt_filter_bar.dart';
import '../widgets/debt_payment_history_sheet.dart';
import '../widgets/pay_debt_dialog.dart';

class UnpaidDebtsPage extends ConsumerStatefulWidget {
  const UnpaidDebtsPage({super.key});

  @override
  ConsumerState<UnpaidDebtsPage> createState() => _UnpaidDebtsPageState();
}

class _UnpaidDebtsPageState extends ConsumerState<UnpaidDebtsPage> {
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
      ref.read(unpaidDebtsProvider.notifier).loadMore();
    }
  }

  void _showCreateSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      barrierColor: AppColors.scrim,
      shape: const RoundedRectangleBorder(borderRadius: AppRadius.sheetRadius),
      builder: (_) => CreateDebtSheet(
        onCreate:
            ({
              required String fName,
              required String amount,
              required String direction,
              String? note,
            }) => ref
                .read(unpaidDebtsProvider.notifier)
                .createDebt(
                  fName: fName,
                  amount: amount,
                  direction: direction,
                  note: note,
                ),
      ),
    );
  }

  void _showPayDialog(DebtModel debt) {
    showDialog(
      context: context,
      builder: (_) => PayDebtDialog(
        debt: debt,
        onPay: (String amount, {String? note}) => ref
            .read(unpaidDebtsProvider.notifier)
            .payDebt(debt.id, amount, note: note),
      ),
    );
  }

  void _showHistorySheet(
    DebtModel debt, {
    required bool isOwner,
    required bool canPay,
    required bool canDelete,
  }) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      barrierColor: AppColors.scrim,
      shape: const RoundedRectangleBorder(borderRadius: AppRadius.sheetRadius),
      builder: (_) => DebtPaymentHistorySheet(
        debt: debt,
        isOwner: isOwner,
        canPay: canPay,
        canDelete: canDelete,
        onPay: (String amount, {String? note}) => ref
            .read(unpaidDebtsProvider.notifier)
            .payDebt(debt.id, amount, note: note),
        onDeleteDebt: canDelete
            ? () {
                Navigator.of(context).pop();
                _confirmDelete(debt);
              }
            : null,
      ),
    );
  }

  Future<void> _confirmDelete(DebtModel debt) async {
    final ok = await showAppConfirmDialog(
      context: context,
      title: 'Qarzni o\'chirish',
      content: AppDialogText(
        emphasis: '"${debt.fName}"',
        text: ' uchun qarz o\'chirilsinmi?',
      ),
      confirmLabel: 'O\'chirish',
      isDanger: true,
    );
    if (ok == true) {
      final err = await ref
          .read(unpaidDebtsProvider.notifier)
          .deleteDebt(debt.id);
      if (err != null && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(parseApiError(err)),
            backgroundColor: AppColors.neg,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(unpaidDebtsProvider);
    final user = ref.watch(authProvider).user;
    final isOwner = user?.isOwner ?? false;
    final canCreate = !isOwner;

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Qarzlar',
        showDrawer: true,
        actions: [
          AppHeaderButton(
            icon: Icons.history_outlined,
            onPressed: () => context.go('/debts/closed'),
            tooltip: 'To\'langan qarzlar',
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
              ref.read(unpaidDebtsProvider.notifier).applyFilter(f),
        ),
      ),
      floatingActionButton: canCreate
          ? FloatingActionButton(
              onPressed: _showCreateSheet,
              tooltip: 'Qarz qo\'shish',
              child: const Icon(Icons.add),
            )
          : null,
      body: Column(
        children: [
          DebtFilterChips(
            filter: state.filter,
            user: user,
            onChanged: (f) =>
                ref.read(unpaidDebtsProvider.notifier).applyFilter(f),
          ),
          Expanded(child: _buildList(state, user)),
        ],
      ),
    );
  }

  Widget _buildList(DebtListState state, dynamic user) {
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
            ref.read(unpaidDebtsProvider.notifier).load(refresh: true),
      );
    }
    if (state.items.isEmpty) {
      return EmptyState(
        message: 'Bu davrda to\'lanmagan qarzlar yo\'q',
        icon: Icons.account_balance_wallet_outlined,
        onRefresh: () =>
            ref.read(unpaidDebtsProvider.notifier).load(refresh: true),
      );
    }

    final isOwner = (user?.isOwner as bool?) ?? false;
    final userId = user?.id as int?;

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () =>
          ref.read(unpaidDebtsProvider.notifier).load(refresh: true),
      child: ListView.separated(
        controller: _scrollCtrl,
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          88,
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
          final isCurrentMonthDebt = isCurrentMonth(debt.addedAt);
          final canPay = isCurrentMonthDebt;
          final canDelete =
              isCurrentMonthDebt && (isOwner || debt.createdById == userId);

          return DebtCard(
            debt: debt,
            canPay: canPay,
            canDelete: canDelete,
            onTap: () => _showHistorySheet(
              debt,
              isOwner: isOwner,
              canPay: canPay,
              canDelete: canDelete,
            ),
            onPay: canPay ? () => _showPayDialog(debt) : null,
            onDelete: canDelete ? () => _confirmDelete(debt) : null,
          );
        },
      ),
    );
  }
}

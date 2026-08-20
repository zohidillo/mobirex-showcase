import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_dialog.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/capital_provider.dart';
import '../widgets/capital_card.dart';
import '../widgets/capital_filter_bar.dart';
import '../widgets/phone_capital_add_sheet.dart';

class PhoneCapitalPage extends ConsumerStatefulWidget {
  const PhoneCapitalPage({super.key});

  @override
  ConsumerState<PhoneCapitalPage> createState() => _PhoneCapitalPageState();
}

class _PhoneCapitalPageState extends ConsumerState<PhoneCapitalPage> {
  final _scrollCtrl = ScrollController();
  bool _showFilters = false;

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollCtrl.position.pixels >=
        _scrollCtrl.position.maxScrollExtent - 200) {
      ref.read(phoneCapitalProvider.notifier).loadMore();
    }
  }

  void _showAddSheet() {
    final user = ref.read(authProvider).user;
    if (user == null) return;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      barrierColor: AppColors.scrim,
      shape: const RoundedRectangleBorder(borderRadius: AppRadius.sheetRadius),
      builder: (_) => PhoneCapitalAddSheet(
        branches: user.branches,
        onAdd: ({required branchId, required amount}) => ref
            .read(phoneCapitalProvider.notifier)
            .addInvestment(branchId: branchId, amount: amount),
      ),
    );
  }

  Future<void> _confirmReset(int branchId) async {
    final ok = await showAppConfirmDialog(
      context: context,
      title: 'Kapitalni nolga tushirasizmi?',
      content: const AppDialogText(
        text:
            'Bu amal faqat joriy oy uchun ishlaydi. '
            'Tikilgan summa 0 bo\'ladi va joriy balansdan tikilgan summa ayriladi.',
      ),
      confirmLabel: 'Tasdiqlash',
      isDanger: true,
    );
    if (ok == true && mounted) {
      final err = await ref
          .read(phoneCapitalProvider.notifier)
          .resetCapital(branchId: branchId);
      if (mounted) {
        if (err != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(parseApiError(err)),
              backgroundColor: AppColors.neg,
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Kapital nolga tushirildi'),
              backgroundColor: AppColors.pos,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(phoneCapitalProvider);
    final user = ref.watch(authProvider).user;

    if (user == null || !user.isOwner) {
      return Scaffold(
        appBar: VelmoraAppBar(subtitle: 'Telefon kapitali', showDrawer: true),
        body: const Center(
          child: Text('Sizga bu sahifaga kirish mumkin emas.'),
        ),
      );
    }

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Telefon kapitali',
        showDrawer: true,
        actions: [
          AppHeaderButton(
            icon: Icons.tune,
            isActive: _showFilters,
            onPressed: () => setState(() => _showFilters = !_showFilters),
            tooltip: 'Filtr',
          ),
        ],
        bottom: CapitalFilterBar(
          state: state,
          branches: user.branches,
          showFilters: _showFilters,
          onFilterChanged: (f) =>
              ref.read(phoneCapitalProvider.notifier).applyFilter(f),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddSheet,
        tooltip: "Kapital qo'shish",
        child: const Icon(Icons.add),
      ),
      body: Column(
        children: [
          CapitalFilterChips(
            state: state,
            branches: user.branches,
            onFilterChanged: (f) =>
                ref.read(phoneCapitalProvider.notifier).applyFilter(f),
          ),
          Expanded(child: _buildList(state)),
        ],
      ),
    );
  }

  Widget _buildList(CapitalListState state) {
    if (state.isLoading) {
      return ListView.separated(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          AppSpacing.s4,
        ),
        itemCount: 4,
        separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.s3),
        itemBuilder: (_, _) => const AppCardSkeleton(),
      );
    }
    if (state.error != null && state.items.isEmpty) {
      return ErrorView(
        message: parseApiError(state.error),
        onRetry: () =>
            ref.read(phoneCapitalProvider.notifier).load(refresh: true),
      );
    }
    if (state.items.isEmpty) {
      return EmptyState(
        message: 'Ma\'lumot topilmadi',
        icon: Icons.account_balance_outlined,
        onRefresh: () =>
            ref.read(phoneCapitalProvider.notifier).load(refresh: true),
      );
    }

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () =>
          ref.read(phoneCapitalProvider.notifier).load(refresh: true),
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
        itemBuilder: (_, i) {
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
          final capital = state.items[i];
          return CapitalCard(
            capital: capital,
            showActions: true,
            onReset: capital.isCurrentMonth && capital.branchId != null
                ? () => _confirmReset(capital.branchId!)
                : null,
          );
        },
      ),
    );
  }
}

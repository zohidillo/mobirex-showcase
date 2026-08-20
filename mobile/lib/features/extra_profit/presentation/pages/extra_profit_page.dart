import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_dialog.dart';
import '../../../../shared/widgets/app_filter_chip.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/models/extra_profit_model.dart';
import '../providers/extra_profit_provider.dart';
import '../widgets/create_extra_profit_sheet.dart';
import '../widgets/extra_profit_card.dart';

class ExtraProfitPage extends ConsumerStatefulWidget {
  const ExtraProfitPage({super.key});

  @override
  ConsumerState<ExtraProfitPage> createState() => _ExtraProfitPageState();
}

class _ExtraProfitPageState extends ConsumerState<ExtraProfitPage> {
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
      ref.read(extraProfitsProvider.notifier).loadMore();
    }
  }

  void _showCreateSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      barrierColor: AppColors.scrim,
      shape: const RoundedRectangleBorder(borderRadius: AppRadius.sheetRadius),
      builder: (_) => CreateExtraProfitSheet(
        onCreate: ({required amount, note}) => ref
            .read(extraProfitsProvider.notifier)
            .createExtraProfit(amount: amount, note: note),
      ),
    );
  }

  Future<void> _confirmDelete(ExtraProfitModel profit) async {
    final ok = await showAppConfirmDialog(
      context: context,
      title: "Qo'shimcha foydani o'chirish",
      content: const AppDialogText(
        text: "Bu qo'shimcha foyda yozuvi o'chirilsinmi?",
      ),
      confirmLabel: "O'chirish",
      isDanger: true,
    );
    if (ok == true) {
      final err = await ref
          .read(extraProfitsProvider.notifier)
          .deleteExtraProfit(profit.id);
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
    final state = ref.watch(extraProfitsProvider);
    final user = ref.watch(authProvider).user;
    final isOwner = user?.isOwner ?? false;
    final isPhoneSeller = user?.isPhoneSeller ?? false;
    final filter = state.filter;
    final notifier = ref.read(extraProfitsProvider.notifier);

    final hasActiveFilter = filter.year != null || filter.branch != null;
    final monthLabel = filter.year != null
        ? '${monthName(filter.month ?? 1)} ${filter.year}'
        : null;
    String? branchLabel;
    if (filter.branch != null && user != null) {
      for (final b in user.branches) {
        if (b.id == filter.branch) branchLabel = b.name;
      }
    }

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: "Qo'shimcha foyda",
        showDrawer: true,
        actions: [
          AppHeaderButton(
            icon: Icons.tune,
            isActive: _showFilters || hasActiveFilter,
            onPressed: () => setState(() => _showFilters = !_showFilters),
            tooltip: 'Filtr',
          ),
        ],
        bottom: _showFilters
            ? AppFilterPanel(
                children: [
                  AppFilterDropdown(
                    label: monthLabel ?? 'Joriy oy',
                    isSet: filter.year != null,
                    onTap: () async {
                      final months = lastMonths();
                      final value = await showAppSelectSheet<String?>(
                        context: context,
                        title: 'Oyni tanlang',
                        selected: filter.year != null
                            ? '${filter.year}/${filter.month}'
                            : null,
                        options: [
                          const AppSelectOption(
                            value: null,
                            label: 'Joriy oy',
                          ),
                          ...months.map(
                            (m) => AppSelectOption(
                              value: '${m['year']}/${m['month']}',
                              label: '${monthName(m['month']!)} ${m['year']}',
                            ),
                          ),
                        ],
                      );
                      if (!context.mounted) return;
                      if (value == null) {
                        notifier.applyFilter(
                          filter.copyWith(clearYearMonth: true),
                        );
                      } else {
                        final p = value.split('/');
                        notifier.applyFilter(
                          filter.copyWith(
                            year: int.parse(p[0]),
                            month: int.parse(p[1]),
                          ),
                        );
                      }
                    },
                  ),
                  if (isOwner && user != null)
                    AppFilterDropdown(
                      label: branchLabel ?? 'Barcha filiallar',
                      isSet: filter.branch != null,
                      onTap: () async {
                        final value = await showAppSelectSheet<int?>(
                          context: context,
                          title: 'Filial',
                          selected: filter.branch,
                          options: [
                            const AppSelectOption(
                              value: null,
                              label: 'Barcha filiallar',
                            ),
                            ...user.branches.map(
                              (b) =>
                                  AppSelectOption(value: b.id, label: b.name),
                            ),
                          ],
                        );
                        if (!context.mounted) return;
                        notifier.applyFilter(
                          filter.copyWith(
                            branch: value,
                            clearBranch: value == null,
                          ),
                        );
                      },
                    ),
                ],
              )
            : null,
      ),
      floatingActionButton: isPhoneSeller
          ? FloatingActionButton(
              onPressed: _showCreateSheet,
              tooltip: "Qo'shimcha foyda qo'shish",
              child: const Icon(Icons.add),
            )
          : null,
      body: Column(
        children: [
          if (hasActiveFilter)
            Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.s4,
                AppSpacing.s3,
                AppSpacing.s4,
                0,
              ),
              child: Wrap(
                spacing: AppSpacing.s2,
                runSpacing: AppSpacing.s2,
                children: [
                  if (monthLabel != null)
                    AppFilterChip(
                      label: monthLabel,
                      onRemove: () => notifier.applyFilter(
                        filter.copyWith(clearYearMonth: true),
                      ),
                    ),
                  if (branchLabel != null)
                    AppFilterChip(
                      label: branchLabel,
                      onRemove: () => notifier.applyFilter(
                        filter.copyWith(clearBranch: true),
                      ),
                    ),
                ],
              ),
            ),
          Expanded(child: _buildList(state, isOwner, isPhoneSeller)),
        ],
      ),
    );
  }

  Widget _buildList(
    ExtraProfitListState state,
    bool isOwner,
    bool isPhoneSeller,
  ) {
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
            ref.read(extraProfitsProvider.notifier).load(refresh: true),
      );
    }
    if (state.items.isEmpty) {
      return EmptyState(
        message: "Bu davrda qo'shimcha foyda yo'q",
        icon: Icons.trending_up_outlined,
        onRefresh: () =>
            ref.read(extraProfitsProvider.notifier).load(refresh: true),
      );
    }

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () =>
          ref.read(extraProfitsProvider.notifier).load(refresh: true),
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
          final profit = state.items[i];
          final canDelete =
              isCurrentMonth(profit.addedAt) && (isOwner || isPhoneSeller);
          return ExtraProfitCard(
            profit: profit,
            canDelete: canDelete,
            onDelete: canDelete ? () => _confirmDelete(profit) : null,
          );
        },
      ),
    );
  }
}

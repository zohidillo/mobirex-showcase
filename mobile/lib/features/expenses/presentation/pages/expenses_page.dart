import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_dialog.dart';
import '../../../../shared/widgets/app_filter_chip.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_total_bar.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/models/expense_model.dart';
import '../providers/expense_provider.dart';
import '../widgets/create_expense_sheet.dart';
import '../widgets/expense_card.dart';

const _typeOptions = <AppSelectOption<String?>>[
  AppSelectOption(value: null, label: 'Barcha turlar'),
  AppSelectOption(value: 'SHOP_EXPENSE', label: "Do'kon xarajati"),
  AppSelectOption(value: 'EMPLOYEE_EXPENSE', label: 'Xodim xarajati'),
];

String? _labelOf(List<AppSelectOption<String?>> options, String? value) {
  if (value == null) return null;
  for (final o in options) {
    if (o.value == value) return o.label;
  }
  return null;
}

class ExpensesPage extends ConsumerStatefulWidget {
  const ExpensesPage({super.key});

  @override
  ConsumerState<ExpensesPage> createState() => _ExpensesPageState();
}

class _ExpensesPageState extends ConsumerState<ExpensesPage> {
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
      ref.read(expensesProvider.notifier).loadMore();
    }
  }

  void _showCreateSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      barrierColor: AppColors.scrim,
      shape: const RoundedRectangleBorder(borderRadius: AppRadius.sheetRadius),
      builder: (_) => CreateExpenseSheet(
        onCreate: ({required type, required amount, note}) => ref
            .read(expensesProvider.notifier)
            .createExpense(type: type, amount: amount, note: note),
      ),
    );
  }

  Future<void> _confirmDelete(ExpenseModel expense) async {
    final ok = await showAppConfirmDialog(
      context: context,
      title: 'Xarajatni o\'chirish',
      content: AppDialogText(
        emphasis: '"${expense.typeDisplay}"',
        text: ' o\'chirilsinmi?',
      ),
      confirmLabel: 'O\'chirish',
      isDanger: true,
    );
    if (ok == true) {
      final err = await ref
          .read(expensesProvider.notifier)
          .deleteExpense(expense.id);
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
    final state = ref.watch(expensesProvider);
    final user = ref.watch(authProvider).user;
    final isOwner = user?.isOwner ?? false;
    final isSeller = user?.isSeller ?? false;
    final filter = state.filter;

    final hasActiveFilter =
        filter.type != null || filter.year != null || filter.branch != null;

    final typeLabel = _labelOf(_typeOptions, filter.type);
    final monthLabel = filter.year != null
        ? '${monthName(filter.month ?? 1)} ${filter.year}'
        : null;
    String? branchLabel;
    if (filter.branch != null && user != null) {
      for (final b in user.branches) {
        if (b.id == filter.branch) branchLabel = b.name;
      }
    }

    final notifier = ref.read(expensesProvider.notifier);

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Xarajatlar',
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
                    label: typeLabel ?? 'Barcha turlar',
                    isSet: filter.type != null,
                    onTap: () async {
                      final value = await showAppSelectSheet<String?>(
                        context: context,
                        title: 'Xarajat turi',
                        selected: filter.type,
                        options: _typeOptions,
                      );
                      if (!context.mounted) return;
                      notifier.applyFilter(
                        filter.copyWith(type: value, clearType: value == null),
                      );
                    },
                  ),
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
      floatingActionButton: isSeller
          ? FloatingActionButton(
              onPressed: _showCreateSheet,
              tooltip: 'Xarajat qo\'shish',
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
                  if (typeLabel != null)
                    AppFilterChip(
                      label: typeLabel,
                      onRemove: () =>
                          notifier.applyFilter(filter.copyWith(clearType: true)),
                    ),
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
          if (state.totalAmount != null)
            AppTotalBar(
              label: 'Jami xarajat',
              value: state.totalAmount!,
              valueColor: AppColors.neg,
            ),
          Expanded(child: _buildList(state, isOwner)),
        ],
      ),
    );
  }

  Widget _buildList(ExpenseListState state, bool isOwner) {
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
        onRetry: () => ref.read(expensesProvider.notifier).load(refresh: true),
      );
    }
    if (state.items.isEmpty) {
      return EmptyState(
        message: 'Bu davrda xarajatlar yo\'q',
        icon: Icons.receipt_outlined,
        onRefresh: () =>
            ref.read(expensesProvider.notifier).load(refresh: true),
      );
    }

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () => ref.read(expensesProvider.notifier).load(refresh: true),
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
          final expense = state.items[i];
          final canDelete = isCurrentMonth(expense.addedAt);
          return ExpenseCard(
            expense: expense,
            canDelete: canDelete,
            onDelete: canDelete ? () => _confirmDelete(expense) : null,
          );
        },
      ),
    );
  }
}

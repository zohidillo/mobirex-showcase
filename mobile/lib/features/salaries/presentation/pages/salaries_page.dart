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
import '../../data/models/salary_model.dart';
import '../providers/salary_provider.dart';
import '../widgets/create_salary_sheet.dart';
import '../widgets/salary_card.dart';

class SalariesPage extends ConsumerStatefulWidget {
  const SalariesPage({super.key});

  @override
  ConsumerState<SalariesPage> createState() => _SalariesPageState();
}

class _SalariesPageState extends ConsumerState<SalariesPage> {
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
      ref.read(salariesProvider.notifier).loadMore();
    }
  }

  void _showCreateSheet(dynamic user) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      barrierColor: AppColors.scrim,
      shape: const RoundedRectangleBorder(borderRadius: AppRadius.sheetRadius),
      builder: (_) => CreateSalarySheet(
        branches: user?.branches ?? [],
        onCreate: ({required employeeId, required amount, note}) => ref
            .read(salariesProvider.notifier)
            .createSalary(employeeId: employeeId, amount: amount, note: note),
      ),
    );
  }

  Future<void> _confirmDelete(SalaryModel salary) async {
    final ok = await showAppConfirmDialog(
      context: context,
      title: 'Oylikni o\'chirish',
      content: AppDialogText(
        emphasis: salary.employee?.displayName ?? 'xodim',
        text: ' ning oyligini o\'chirishni tasdiqlaysizmi?',
      ),
      confirmLabel: 'O\'chirish',
      isDanger: true,
    );
    if (ok == true) {
      final err = await ref
          .read(salariesProvider.notifier)
          .deleteSalary(salary.id);
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
    final state = ref.watch(salariesProvider);
    final user = ref.watch(authProvider).user;
    final isOwner = user?.isOwner ?? false;
    final filter = state.filter;
    final notifier = ref.read(salariesProvider.notifier);
    final currentYear = DateTime.now().year;
    final years = List.generate(4, (i) => currentYear - i);

    final hasActiveFilter = filter.month != null || filter.branch != null;
    final monthLabel = filter.month != null ? monthName(filter.month!) : null;
    String? branchLabel;
    if (filter.branch != null && user != null) {
      for (final b in user.branches) {
        if (b.id == filter.branch) branchLabel = b.name;
      }
    }

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Oyliklar',
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
                    label: '${filter.year ?? currentYear}',
                    isSet: true,
                    onTap: () async {
                      final value = await showAppSelectSheet<int>(
                        context: context,
                        title: 'Yilni tanlang',
                        selected: filter.year ?? currentYear,
                        options: years
                            .map(
                              (y) => AppSelectOption(value: y, label: '$y'),
                            )
                            .toList(),
                      );
                      if (!context.mounted || value == null) return;
                      notifier.applyFilter(filter.copyWith(year: value));
                    },
                  ),
                  AppFilterDropdown(
                    label: monthLabel ?? 'Barcha oylar',
                    isSet: filter.month != null,
                    onTap: () async {
                      final months = lastMonths(count: 12);
                      final value = await showAppSelectSheet<int?>(
                        context: context,
                        title: 'Oyni tanlang',
                        selected: filter.month,
                        options: [
                          const AppSelectOption(
                            value: null,
                            label: 'Barcha oylar',
                          ),
                          ...months.map(
                            (m) => AppSelectOption(
                              value: m['month'],
                              label: monthName(m['month']!),
                            ),
                          ),
                        ],
                      );
                      if (!context.mounted) return;
                      notifier.applyFilter(
                        filter.copyWith(
                          month: value,
                          clearMonth: value == null,
                        ),
                      );
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
      floatingActionButton: isOwner
          ? FloatingActionButton(
              onPressed: () => _showCreateSheet(user),
              tooltip: 'Oylik qo\'shish',
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
                        filter.copyWith(clearMonth: true),
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
          Expanded(child: _buildList(state, isOwner)),
        ],
      ),
    );
  }

  Widget _buildList(SalaryListState state, bool isOwner) {
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
        onRetry: () => ref.read(salariesProvider.notifier).load(refresh: true),
      );
    }
    if (state.items.isEmpty) {
      return EmptyState(
        message: 'Oyliklar topilmadi',
        icon: Icons.payments_outlined,
        onRefresh: () =>
            ref.read(salariesProvider.notifier).load(refresh: true),
      );
    }

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () => ref.read(salariesProvider.notifier).load(refresh: true),
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
          final salary = state.items[i];
          final canDelete = isOwner && isCurrentMonth(salary.addedAt);
          return SalaryCard(
            salary: salary,
            canDelete: canDelete,
            onDelete: canDelete ? () => _confirmDelete(salary) : null,
          );
        },
      ),
    );
  }
}

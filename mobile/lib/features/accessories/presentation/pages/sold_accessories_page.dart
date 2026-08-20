import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/router/navigation_helper.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/providers/category_provider.dart';
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
import '../../data/models/accessory_sale_model.dart';
import '../providers/accessory_provider.dart';
import '../widgets/accessory_card.dart';

class SoldAccessoriesPage extends ConsumerStatefulWidget {
  const SoldAccessoriesPage({super.key});

  @override
  ConsumerState<SoldAccessoriesPage> createState() =>
      _SoldAccessoriesPageState();
}

class _SoldAccessoriesPageState extends ConsumerState<SoldAccessoriesPage> {
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
      ref.read(soldAccessoriesProvider.notifier).loadMore();
    }
  }

  void _apply(AccessoryFilter filter) =>
      ref.read(soldAccessoriesProvider.notifier).applyFilter(filter);

  Future<void> _confirmReturn(AccessorySaleModel sale) async {
    final ok = await showAppConfirmDialog(
      context: context,
      title: 'Sotuvni qaytarish',
      content: AppDialogText(
        emphasis: sale.accessory?.name ?? 'aksessuar',
        text: ' (miqdor: ${sale.quantity}) qaytarilsinmi?',
      ),
      confirmLabel: 'Qaytarish',
      isDanger: true,
    );
    if (ok == true) {
      final err = await ref
          .read(soldAccessoriesProvider.notifier)
          .returnSale(sale.id);
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
    final state = ref.watch(soldAccessoriesProvider);
    final user = ref.watch(authProvider).user;
    final showBranchFilter =
        user != null && (user.isOwner || user.hasMultipleBranches);
    final categories = ref.watch(accessoryCategoriesProvider).categories;
    final filter = state.filter;

    final hasActiveFilter =
        filter.category != null ||
        filter.year != null ||
        filter.branch != null;

    String? categoryLabel;
    if (filter.category != null) {
      for (final c in categories) {
        if (c.id == filter.category) categoryLabel = c.name;
      }
    }
    String? branchLabel;
    if (filter.branch != null && user != null) {
      for (final b in user.branches) {
        if (b.id == filter.branch) branchLabel = b.name;
      }
    }
    final monthLabel = filter.year != null
        ? '${monthName(filter.month ?? 1)} ${filter.year}'
        : null;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) goBack(context, ref);
      },
      child: Scaffold(
        appBar: VelmoraAppBar(
          subtitle: 'Sotilgan aksessuarlar',
          showDrawer: true,
          actions: [
            AppHeaderButton(
              icon: Icons.cable_outlined,
              onPressed: () => context.go('/accessories/unsold'),
              tooltip: 'Ombordagi aksessuarlar',
            ),
          ],
          bottom: AppHeaderBottom(
            children: [
              AppSearchBar(
                controller: _searchCtrl,
                hintText: 'Qidirish...',
                isFilterActive: _showFilters || hasActiveFilter,
                onChanged: (q) =>
                    _apply(filter.copyWith(search: q.isEmpty ? null : q)),
                onClear: () {
                  _searchCtrl.clear();
                  _apply(filter.copyWith(clearSearch: true));
                },
                onFilterTap: () => setState(() => _showFilters = !_showFilters),
              ),
              if (_showFilters)
                AppFilterPanel(
                  children: [
                    if (categories.isNotEmpty)
                      AppFilterDropdown(
                        label: categoryLabel ?? 'Kategoriya',
                        isSet: filter.category != null,
                        onTap: () async {
                          final value = await showAppSelectSheet<int?>(
                            context: context,
                            title: 'Kategoriya',
                            selected: filter.category,
                            options: [
                              const AppSelectOption(
                                value: null,
                                label: 'Barcha kategoriyalar',
                              ),
                              ...categories.map(
                                (c) =>
                                    AppSelectOption(value: c.id, label: c.name),
                              ),
                            ],
                          );
                          if (!context.mounted) return;
                          _apply(
                            filter.copyWith(
                              category: value,
                              clearCategory: value == null,
                            ),
                          );
                        },
                      ),
                    AppFilterDropdown(
                      label: monthLabel ?? 'Oy',
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
                          _apply(filter.copyWith(clearYearMonth: true));
                        } else {
                          final parts = value.split('/');
                          _apply(
                            filter.copyWith(
                              year: int.parse(parts[0]),
                              month: int.parse(parts[1]),
                            ),
                          );
                        }
                      },
                    ),
                    if (showBranchFilter)
                      AppFilterDropdown(
                        label: branchLabel ?? 'Filial',
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
                          _apply(
                            filter.copyWith(
                              branch: value,
                              clearBranch: value == null,
                            ),
                          );
                        },
                      ),
                  ],
                ),
            ],
          ),
        ),
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
                    if (categoryLabel != null)
                      AppFilterChip(
                        label: categoryLabel,
                        onRemove: () =>
                            _apply(filter.copyWith(clearCategory: true)),
                      ),
                    if (monthLabel != null)
                      AppFilterChip(
                        label: monthLabel,
                        onRemove: () =>
                            _apply(filter.copyWith(clearYearMonth: true)),
                      ),
                    if (branchLabel != null)
                      AppFilterChip(
                        label: branchLabel,
                        onRemove: () =>
                            _apply(filter.copyWith(clearBranch: true)),
                      ),
                  ],
                ),
              ),
            Expanded(child: _buildList(state)),
          ],
        ),
      ),
    );
  }

  Widget _buildList(SoldAccessoryListState state) {
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
            ref.read(soldAccessoriesProvider.notifier).load(refresh: true),
      );
    }
    if (state.items.isEmpty) {
      return EmptyState(
        message: 'Bu davrda sotilgan aksessuarlar yo\'q',
        icon: Icons.receipt_long_outlined,
        onRefresh: () =>
            ref.read(soldAccessoriesProvider.notifier).load(refresh: true),
      );
    }

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () =>
          ref.read(soldAccessoriesProvider.notifier).load(refresh: true),
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
          final sale = state.items[i];
          final canReturn = isCurrentMonth(sale.soldAt);
          return SoldAccessoryCard(
            sale: sale,
            canReturn: canReturn,
            onReturn: canReturn ? () => _confirmReturn(sale) : null,
          );
        },
      ),
    );
  }
}

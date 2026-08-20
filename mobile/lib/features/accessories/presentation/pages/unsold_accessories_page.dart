import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/providers/category_provider.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_dialog.dart';
import '../../../../shared/widgets/app_filter_chip.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/models/accessory_model.dart';
import '../providers/accessory_provider.dart';
import '../widgets/accessory_card.dart';
import '../widgets/sell_accessory_dialog.dart';

class UnsoldAccessoriesPage extends ConsumerStatefulWidget {
  const UnsoldAccessoriesPage({super.key});

  @override
  ConsumerState<UnsoldAccessoriesPage> createState() =>
      _UnsoldAccessoriesPageState();
}

class _UnsoldAccessoriesPageState extends ConsumerState<UnsoldAccessoriesPage> {
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
      ref.read(unsoldAccessoriesProvider.notifier).loadMore();
    }
  }

  void _apply(AccessoryFilter filter) =>
      ref.read(unsoldAccessoriesProvider.notifier).applyFilter(filter);

  void _showSellSheet(BuildContext context, AccessoryModel accessory) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      barrierColor: AppColors.scrim,
      shape: const RoundedRectangleBorder(
        borderRadius: AppRadius.sheetRadius,
      ),
      builder: (_) => SellAccessorySheet(
        accessory: accessory,
        onSell: (qty, price) => ref
            .read(unsoldAccessoriesProvider.notifier)
            .sellAccessory(accessory.id, qty, price),
      ),
    );
  }

  Future<void> _confirmDelete(AccessoryModel accessory) async {
    final ok = await showAppConfirmDialog(
      context: context,
      title: 'Aksessuar o\'chirish',
      content: AppDialogText(
        emphasis: accessory.name,
        text: ' o\'chirilsinmi? Sarmoya qaytariladi.',
      ),
      confirmLabel: 'O\'chirish',
      isDanger: true,
    );
    if (ok == true) {
      final err = await ref
          .read(unsoldAccessoriesProvider.notifier)
          .deleteAccessory(accessory.id);
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
    final state = ref.watch(unsoldAccessoriesProvider);
    final user = ref.watch(authProvider).user;
    final showBranchFilter =
        user != null && (user.isOwner || user.hasMultipleBranches);
    final categories = ref.watch(accessoryCategoriesProvider).categories;
    final filter = state.filter;

    final hasActiveFilter =
        filter.category != null || filter.branch != null;

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

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Ombordagi aksessuarlar',
        showDrawer: true,
        actions: [
          AppHeaderButton(
            icon: Icons.receipt_long_outlined,
            onPressed: () => context.go('/accessories/sold'),
            tooltip: 'Sotilgan aksessuarlar',
          ),
        ],
        bottom: AppHeaderBottom(
          children: [
            AppSearchBar(
              controller: _searchCtrl,
              hintText: 'Aksessuar qidirish...',
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
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/accessories/add'),
        tooltip: 'Aksessuar qo\'shish',
        child: const Icon(Icons.add),
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
    );
  }

  Widget _buildList(AccessoryListState state) {
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
            ref.read(unsoldAccessoriesProvider.notifier).load(refresh: true),
      );
    }
    if (state.items.isEmpty) {
      return EmptyState(
        message: 'Omborda aksessuarlar yo\'q',
        icon: Icons.cable_outlined,
        onRefresh: () =>
            ref.read(unsoldAccessoriesProvider.notifier).load(refresh: true),
      );
    }

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () =>
          ref.read(unsoldAccessoriesProvider.notifier).load(refresh: true),
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
          final acc = state.items[i];
          return UnsoldAccessoryCard(
            accessory: acc,
            onSell: () => _showSellSheet(ctx, acc),
            onDelete: () => _confirmDelete(acc),
          );
        },
      ),
    );
  }
}

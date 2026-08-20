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
import '../../data/models/phone_model.dart';
import '../providers/phone_provider.dart';
import '../widgets/phone_card.dart';
import '../widgets/sell_phone_dialog.dart';

/// Xotira variantlari — eski `DropdownButton` ro'yxati bilan bir xil.
const _storageOptions = <AppSelectOption<String?>>[
  AppSelectOption(value: null, label: 'Barcha xotira'),
  AppSelectOption(value: '16', label: '16 GB'),
  AppSelectOption(value: '32', label: '32 GB'),
  AppSelectOption(value: '64', label: '64 GB'),
  AppSelectOption(value: '128', label: '128 GB'),
  AppSelectOption(value: '256', label: '256 GB'),
  AppSelectOption(value: '512', label: '512 GB'),
  AppSelectOption(value: '1024', label: '1 TB'),
  AppSelectOption(value: '2048', label: '2 TB'),
];

class UnsoldPhonesPage extends ConsumerStatefulWidget {
  const UnsoldPhonesPage({super.key});

  @override
  ConsumerState<UnsoldPhonesPage> createState() => _UnsoldPhonesPageState();
}

class _UnsoldPhonesPageState extends ConsumerState<UnsoldPhonesPage> {
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
      ref.read(unsoldPhonesProvider.notifier).loadMore();
    }
  }

  void _apply(PhoneFilter filter) =>
      ref.read(unsoldPhonesProvider.notifier).applyFilter(filter);

  void _showSellSheet(BuildContext context, PhoneModel phone) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      barrierColor: AppColors.scrim,
      shape: const RoundedRectangleBorder(
        borderRadius: AppRadius.sheetRadius,
      ),
      builder: (_) => SellPhoneSheet(
        phone: phone,
        onSell: (price) =>
            ref.read(unsoldPhonesProvider.notifier).sellPhone(phone.id, price),
      ),
    );
  }

  Future<void> _confirmDelete(PhoneModel phone) async {
    final ok = await showAppConfirmDialog(
      context: context,
      title: 'Telefon o\'chirish',
      content: AppDialogText(
        emphasis: phone.name,
        text: ' o\'chirilsinmi? Narx kapitalga qaytariladi.',
      ),
      confirmLabel: 'O\'chirish',
      isDanger: true,
    );
    if (ok == true) {
      final err = await ref
          .read(unsoldPhonesProvider.notifier)
          .deletePhone(phone.id);
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
    final state = ref.watch(unsoldPhonesProvider);
    final user = ref.watch(authProvider).user;
    final showBranchFilter =
        user != null && (user.isOwner || user.hasMultipleBranches);
    final categories = ref.watch(phoneCategoriesProvider).categories;
    final filter = state.filter;

    final hasActiveFilter =
        filter.category != null ||
        filter.storage != null ||
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
    String? storageLabel;
    if (filter.storage != null) {
      for (final o in _storageOptions) {
        if (o.value == filter.storage) storageLabel = o.label;
      }
    }

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Sotilmagan telefonlar',
        showDrawer: true,
        actions: [
          AppHeaderButton(
            icon: Icons.view_list_outlined,
            onPressed: () => context.go('/phones/sold'),
            tooltip: 'Sotilgan telefonlar',
          ),
        ],
        bottom: AppHeaderBottom(
          children: [
            AppSearchBar(
              controller: _searchCtrl,
              hintText: 'Nom yoki IMEI bo\'yicha qidirish...',
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
                              (c) => AppSelectOption(
                                value: c.id,
                                label: c.name,
                              ),
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
                    label: storageLabel ?? 'Xotira',
                    isSet: filter.storage != null,
                    onTap: () async {
                      final value = await showAppSelectSheet<String?>(
                        context: context,
                        title: 'Xotira',
                        selected: filter.storage,
                        options: _storageOptions,
                      );
                      if (!context.mounted) return;
                      _apply(
                        filter.copyWith(
                          storage: value,
                          clearStorage: value == null,
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
                              (b) => AppSelectOption(
                                value: b.id,
                                label: b.name,
                              ),
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
        onPressed: () => context.go('/phones/add'),
        tooltip: 'Telefon qo\'shish',
        child: const Icon(Icons.add),
      ),
      body: Column(
        children: [
          // Faol filtr chiplari — defekt tuzatildi (`.chips`).
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
                      onRemove: () => _apply(
                        filter.copyWith(clearCategory: true),
                      ),
                    ),
                  if (storageLabel != null)
                    AppFilterChip(
                      label: storageLabel,
                      onRemove: () =>
                          _apply(filter.copyWith(clearStorage: true)),
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

  Widget _buildList(PhoneListState state) {
    if (state.isLoading) {
      // Yuklanish — skeleton kartalar (spinner emas).
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
    if (state.error != null && state.phones.isEmpty) {
      return ErrorView(
        message: parseApiError(state.error),
        onRetry: () =>
            ref.read(unsoldPhonesProvider.notifier).load(refresh: true),
      );
    }
    if (state.phones.isEmpty) {
      return EmptyState(
        message: 'Sotilmagan telefonlar topilmadi',
        icon: Icons.phone_android,
        onRefresh: () =>
            ref.read(unsoldPhonesProvider.notifier).load(refresh: true),
      );
    }

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () =>
          ref.read(unsoldPhonesProvider.notifier).load(refresh: true),
      child: ListView.separated(
        controller: _scrollCtrl,
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          88,
        ),
        itemCount: state.phones.length + (state.isLoadingMore ? 1 : 0),
        separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.s3),
        itemBuilder: (ctx, i) {
          if (i == state.phones.length) {
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
          final phone = state.phones[i];
          return UnsoldPhoneCard(
            phone: phone,
            onSell: () => _showSellSheet(ctx, phone),
            onDelete: () => _confirmDelete(phone),
          );
        },
      ),
    );
  }
}

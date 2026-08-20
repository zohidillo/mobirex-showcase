import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/widgets/app_filter_chip.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../providers/debt_provider.dart';

/// Yo'nalish variantlari — eski `DropdownButton` ro'yxati bilan bir xil.
const _directionOptions = <AppSelectOption<String?>>[
  AppSelectOption(value: null, label: 'Barchasi'),
  AppSelectOption(value: 'WE_GAVE', label: 'Biz berdik'),
  AppSelectOption(value: 'WE_TOOK', label: 'Biz oldik'),
];

const _domainOptions = <AppSelectOption<String?>>[
  AppSelectOption(value: null, label: 'Barchasi'),
  AppSelectOption(value: 'PHONE', label: 'Telefon'),
  AppSelectOption(value: 'ACCESSORY', label: 'Aksessuar'),
];

String? _labelOf(List<AppSelectOption<String?>> options, String? value) {
  if (value == null) return null;
  for (final o in options) {
    if (o.value == value) return o.label;
  }
  return null;
}

/// Qarzlar qidiruv + filtr bari — `redesign4/debts/unpaid-debts.html`.
///
/// Yangi dizaynda bu blok header (`.hdr`) ichida turadi, shuning uchun
/// `PreferredSizeWidget`: `VelmoraAppBar(bottom: DebtFilterBar(...))`.
/// Konstruktor parametrlari o'zgarmadi.
class DebtFilterBar extends StatelessWidget implements PreferredSizeWidget {
  final TextEditingController searchCtrl;
  final DebtListState state;
  final bool showBranch;
  final bool showDomain;
  final dynamic user;
  final void Function(DebtFilter) onChanged;

  /// Filtr paneli ochiqmi. Holat sahifada saqlanadi — shundagina
  /// [preferredSize] to'g'ri hisoblanadi (header balandligi o'zgaradi).
  final bool showFilters;
  final VoidCallback onToggleFilters;

  const DebtFilterBar({
    super.key,
    required this.searchCtrl,
    required this.state,
    required this.showBranch,
    required this.showDomain,
    required this.user,
    required this.onChanged,
    required this.showFilters,
    required this.onToggleFilters,
  });

  /// Qidiruv qatori 54px + ochiq bo'lsa filtr paneli 50px.
  @override
  Size get preferredSize => Size.fromHeight(showFilters ? 104 : 54);

  DebtFilter get _filter => state.filter;

  @override
  Widget build(BuildContext context) {
    final hasActiveFilter =
        _filter.direction != null ||
        _filter.year != null ||
        _filter.domain != null ||
        _filter.branch != null;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        AppSearchBar(
          controller: searchCtrl,
          hintText: 'Ism bo\'yicha qidirish...',
          isFilterActive: showFilters || hasActiveFilter,
          onChanged: (q) =>
              onChanged(_filter.copyWith(search: q.isEmpty ? null : q)),
          onClear: () {
            searchCtrl.clear();
            onChanged(_filter.copyWith(clearSearch: true));
          },
          onFilterTap: onToggleFilters,
        ),
        if (showFilters)
          AppFilterPanel(
            children: [
              AppFilterDropdown(
                label:
                    _labelOf(_directionOptions, _filter.direction) ??
                    'Yo\'nalish',
                isSet: _filter.direction != null,
                onTap: () async {
                  final value = await showAppSelectSheet<String?>(
                    context: context,
                    title: 'Yo\'nalish',
                    selected: _filter.direction,
                    options: _directionOptions,
                  );
                  if (!context.mounted) return;
                  onChanged(
                    _filter.copyWith(
                      direction: value,
                      clearDirection: value == null,
                    ),
                  );
                },
              ),
              AppFilterDropdown(
                label: _filter.year != null
                    ? '${monthName(_filter.month ?? 1)} ${_filter.year}'
                    : 'Oy',
                isSet: _filter.year != null,
                onTap: () async {
                  final months = lastMonths();
                  final value = await showAppSelectSheet<String?>(
                    context: context,
                    title: 'Oyni tanlang',
                    selected: _filter.year != null
                        ? '${_filter.year}/${_filter.month}'
                        : null,
                    options: [
                      const AppSelectOption(value: null, label: 'Joriy oy'),
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
                    onChanged(_filter.copyWith(clearYearMonth: true));
                  } else {
                    final parts = value.split('/');
                    onChanged(
                      _filter.copyWith(
                        year: int.parse(parts[0]),
                        month: int.parse(parts[1]),
                      ),
                    );
                  }
                },
              ),
              if (showDomain)
                AppFilterDropdown(
                  label: _labelOf(_domainOptions, _filter.domain) ?? 'Bo\'lim',
                  isSet: _filter.domain != null,
                  onTap: () async {
                    final value = await showAppSelectSheet<String?>(
                      context: context,
                      title: 'Bo\'lim',
                      selected: _filter.domain,
                      options: _domainOptions,
                    );
                    if (!context.mounted) return;
                    onChanged(
                      _filter.copyWith(
                        domain: value,
                        clearDomain: value == null,
                      ),
                    );
                  },
                ),
              if (showBranch && user?.branches != null)
                AppFilterDropdown(
                  label: _branchLabel() ?? 'Filial',
                  isSet: _filter.branch != null,
                  onTap: () async {
                    final value = await showAppSelectSheet<int?>(
                      context: context,
                      title: 'Filial',
                      selected: _filter.branch,
                      options: [
                        const AppSelectOption(
                          value: null,
                          label: 'Barcha filiallar',
                        ),
                        ...(user!.branches as List).map(
                          (b) => AppSelectOption<int?>(
                            value: b.id as int,
                            label: b.name as String,
                          ),
                        ),
                      ],
                    );
                    if (!context.mounted) return;
                    onChanged(
                      _filter.copyWith(
                        branch: value,
                        clearBranch: value == null,
                      ),
                    );
                  },
                ),
            ],
          ),
      ],
    );
  }

  String? _branchLabel() {
    if (_filter.branch == null || user?.branches == null) return null;
    for (final b in user!.branches as List) {
      if (b.id == _filter.branch) return b.name as String;
    }
    return null;
  }
}

/// Faol filtr chiplari — `.chips` (defekt tuzatildi).
///
/// Ro'yxat ustida, `body` ichida ko'rsatiladi.
class DebtFilterChips extends StatelessWidget {
  const DebtFilterChips({
    super.key,
    required this.filter,
    required this.user,
    required this.onChanged,
  });

  final DebtFilter filter;
  final dynamic user;
  final void Function(DebtFilter) onChanged;

  String? _branchLabel() {
    if (filter.branch == null || user?.branches == null) return null;
    for (final b in user!.branches as List) {
      if (b.id == filter.branch) return b.name as String;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final directionLabel = _labelOf(_directionOptions, filter.direction);
    final domainLabel = _labelOf(_domainOptions, filter.domain);
    final monthLabel = filter.year != null
        ? '${monthName(filter.month ?? 1)} ${filter.year}'
        : null;
    final branchLabel = _branchLabel();

    final chips = <Widget>[
      if (directionLabel != null)
        AppFilterChip(
          label: directionLabel,
          onRemove: () => onChanged(filter.copyWith(clearDirection: true)),
        ),
      if (monthLabel != null)
        AppFilterChip(
          label: monthLabel,
          onRemove: () => onChanged(filter.copyWith(clearYearMonth: true)),
        ),
      if (domainLabel != null)
        AppFilterChip(
          label: domainLabel,
          onRemove: () => onChanged(filter.copyWith(clearDomain: true)),
        ),
      if (branchLabel != null)
        AppFilterChip(
          label: branchLabel,
          onRemove: () => onChanged(filter.copyWith(clearBranch: true)),
        ),
    ];

    if (chips.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.s4,
        AppSpacing.s3,
        AppSpacing.s4,
        0,
      ),
      child: Wrap(
        spacing: AppSpacing.s2,
        runSpacing: AppSpacing.s2,
        children: chips,
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../features/profile/data/models/user_model.dart';
import '../../../../shared/widgets/app_filter_chip.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../providers/capital_provider.dart';

/// Kapital filtri — `redesign4/capital/phone-capital.html` (2-3 frame).
///
/// Header ichida turadi (`VelmoraAppBar.bottom`), shuning uchun
/// `PreferredSizeWidget`. Panel holati sahifada saqlanadi — balandlik
/// to'g'ri hisoblanishi uchun.
class CapitalFilterBar extends StatelessWidget implements PreferredSizeWidget {
  final CapitalListState state;
  final List<UserBranch> branches;
  final void Function(CapitalFilter) onFilterChanged;
  final bool showFilters;

  const CapitalFilterBar({
    super.key,
    required this.state,
    required this.branches,
    required this.onFilterChanged,
    this.showFilters = true,
  });

  static List<int> get _years {
    final now = DateTime.now();
    return List.generate(5, (i) => now.year - i);
  }

  @override
  Size get preferredSize => Size.fromHeight(showFilters ? 50 : 0);

  @override
  Widget build(BuildContext context) {
    if (!showFilters) return const SizedBox.shrink();
    final filter = state.filter;

    return AppFilterPanel(
      children: [
        AppFilterDropdown(
          label: filter.year != null ? '${filter.year}' : 'Joriy yil',
          isSet: filter.year != null,
          onTap: () async {
            final value = await showAppSelectSheet<int?>(
              context: context,
              title: 'Yilni tanlang',
              selected: filter.year,
              options: [
                const AppSelectOption(value: null, label: 'Joriy yil'),
                ..._years.map((y) => AppSelectOption(value: y, label: '$y')),
              ],
            );
            if (!context.mounted) return;
            onFilterChanged(
              filter.copyWith(year: value, clearYear: value == null),
            );
          },
        ),
        if (branches.length > 1)
          AppFilterDropdown(
            label: _branchLabel() ?? 'Barcha filiallar',
            isSet: filter.branchId != null,
            onTap: () async {
              final value = await showAppSelectSheet<int?>(
                context: context,
                title: 'Filial',
                selected: filter.branchId,
                options: [
                  const AppSelectOption(
                    value: null,
                    label: 'Barcha filiallar',
                  ),
                  ...branches.map(
                    (b) => AppSelectOption<int?>(value: b.id, label: b.name),
                  ),
                ],
              );
              if (!context.mounted) return;
              onFilterChanged(
                filter.copyWith(branchId: value, clearBranch: value == null),
              );
            },
          ),
      ],
    );
  }

  String? _branchLabel() {
    if (state.filter.branchId == null) return null;
    for (final b in branches) {
      if (b.id == state.filter.branchId) return b.name;
    }
    return null;
  }
}

/// Faol filtr chiplari — `.chips`.
class CapitalFilterChips extends StatelessWidget {
  const CapitalFilterChips({
    super.key,
    required this.state,
    required this.branches,
    required this.onFilterChanged,
  });

  final CapitalListState state;
  final List<UserBranch> branches;
  final void Function(CapitalFilter) onFilterChanged;

  @override
  Widget build(BuildContext context) {
    final filter = state.filter;
    String? branchLabel;
    for (final b in branches) {
      if (b.id == filter.branchId) branchLabel = b.name;
    }

    final chips = <Widget>[
      if (filter.year != null)
        AppFilterChip(
          label: '${filter.year}',
          onRemove: () => onFilterChanged(filter.copyWith(clearYear: true)),
        ),
      if (branchLabel != null)
        AppFilterChip(
          label: branchLabel,
          onRemove: () => onFilterChanged(filter.copyWith(clearBranch: true)),
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

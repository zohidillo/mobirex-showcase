import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/app_select_sheet.dart';

const _monthNames = [
  '',
  'Yanvar',
  'Fevral',
  'Mart',
  'Aprel',
  'May',
  'Iyun',
  'Iyul',
  'Avgust',
  'Sentabr',
  'Oktabr',
  'Noyabr',
  'Dekabr',
];

/// Dashboard yil/oy filtri — `redesign3/staff-dashboard.html` `.dfilter`.
///
/// Pill dropdownlar (`.ddrop` — 40px, card fon, soya bilan), bosilganda
/// `.bsheet` tanlash varag'i ochiladi. Mantiq (`onChanged`) o'zgarmadi.
class DashboardFilterBar extends StatelessWidget {
  final int selectedYear;
  final int selectedMonth;
  final void Function(int year, int month) onChanged;

  const DashboardFilterBar({
    super.key,
    required this.selectedYear,
    required this.selectedMonth,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _DashboardDrop(
          label: '$selectedYear',
          onTap: () => _showYearPicker(context),
        ),
        const SizedBox(width: AppSpacing.s2),
        _DashboardDrop(
          label: _monthNames[selectedMonth],
          onTap: () => _showMonthPicker(context),
        ),
      ],
    );
  }

  Future<void> _showYearPicker(BuildContext context) async {
    final currentYear = DateTime.now().year;
    final years = List.generate(
      4,
      (i) => currentYear - 3 + i + 1,
    ).reversed.toList();

    final value = await showAppSelectSheet<int>(
      context: context,
      title: 'Yilni tanlang',
      selected: selectedYear,
      options: years
          .map((y) => AppSelectOption(value: y, label: '$y'))
          .toList(),
    );
    if (value == null) return;
    onChanged(value, selectedMonth);
  }

  Future<void> _showMonthPicker(BuildContext context) async {
    final value = await showAppSelectSheet<int>(
      context: context,
      title: 'Oyni tanlang',
      selected: selectedMonth,
      options: List.generate(
        12,
        (i) => AppSelectOption(value: i + 1, label: _monthNames[i + 1]),
      ),
    );
    if (value == null) return;
    onChanged(selectedYear, value);
  }
}

/// `.ddrop` — 40px · `--card` fon · 13/700 `--ink` · soya.
class _DashboardDrop extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _DashboardDrop({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      type: MaterialType.transparency,
      child: InkWell(
        onTap: onTap,
        borderRadius: AppRadius.chipRadius,
        child: Container(
          height: 44,
          padding: const EdgeInsets.symmetric(horizontal: 14),
          decoration: const BoxDecoration(
            color: AppColors.card,
            borderRadius: AppRadius.chipRadius,
            boxShadow: AppShadows.card,
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: AppColors.ink,
                ),
              ),
              const SizedBox(width: AppSpacing.s2),
              const Icon(
                Icons.expand_more,
                size: 14,
                color: AppColors.ink3,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Jami banner — `r4.css` `.totalbar`.
///
/// `--surface` fon · 12px radius · bitta soya · yorliq 11/800 UPPERCASE
/// (`--ink-3`) · qiymat 22/800 tabular (`--pos` / `--neg` / `--ink`).
class AppTotalBar extends StatelessWidget {
  const AppTotalBar({
    super.key,
    required this.label,
    required this.value,
    this.valueColor,
    this.margin = const EdgeInsets.fromLTRB(
      AppSpacing.s4,
      14,
      AppSpacing.s4,
      0,
    ),
  });

  final String label;
  final String value;
  final Color? valueColor;
  final EdgeInsetsGeometry margin;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: margin,
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s4,
        vertical: 13,
      ),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppRadius.cardRadius,
        boxShadow: AppShadows.card,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.baseline,
        textBaseline: TextBaseline.alphabetic,
        children: [
          Expanded(
            child: Text(
              label.toUpperCase(),
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                letterSpacing: 1.32,
                color: AppColors.ink3,
              ),
            ),
          ),
          const SizedBox(width: 10),
          Text(
            value,
            style: AppText.totalValue.copyWith(color: valueColor),
          ),
        ],
      ),
    );
  }
}

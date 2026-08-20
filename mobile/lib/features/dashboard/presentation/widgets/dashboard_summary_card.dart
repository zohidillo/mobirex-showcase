import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

/// Metrik karta — `redesign3/staff-dashboard.html` `.mb`.
///
/// `--card` fon · 12px radius · bitta soya · yorliq 11.5 (`--ink-2`) ·
/// qiymat 24/800 tabular. Bosilganda fill +1 pog'ona va 1px siljish.
///
/// Konstruktor o'zgarmadi — `icon` / `iconBgColor` hamon qabul qilinadi,
/// lekin yangi dizaynda metrik kartada ikon yo'q (13-qoida: bitta namuna),
/// shuning uchun ular chizilmaydi.
class DashboardSummaryCard extends StatefulWidget {
  final String label;
  final String value;
  final Color? valueColor;
  final IconData? icon;
  final Color? iconBgColor;
  final VoidCallback? onTap;

  const DashboardSummaryCard({
    super.key,
    required this.label,
    required this.value,
    this.valueColor,
    this.icon,
    this.iconBgColor,
    this.onTap,
  });

  @override
  State<DashboardSummaryCard> createState() => _DashboardSummaryCardState();
}

class _DashboardSummaryCardState extends State<DashboardSummaryCard> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final pressed = _pressed && widget.onTap != null;

    return AnimatedContainer(
      duration: AppDurations.press,
      curve: AppCurves.press,
      transform: Matrix4.translationValues(0, pressed ? 1 : 0, 0),
      decoration: BoxDecoration(
        color: pressed ? AppColors.cardPressed : AppColors.card,
        borderRadius: AppRadius.cardRadius,
        boxShadow: pressed ? AppShadows.cardPressed : AppShadows.card,
      ),
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          onTap: widget.onTap,
          onHighlightChanged: (v) {
            if (_pressed != v) setState(() => _pressed = v);
          },
          borderRadius: AppRadius.cardRadius,
          splashColor: Colors.transparent,
          highlightColor: Colors.transparent,
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.s4,
              vertical: 14,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  widget.label,
                  style: const TextStyle(
                    color: AppColors.ink2,
                    fontSize: 11.5,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 5),
                Text(
                  widget.value,
                  style: AppText.metricValue.copyWith(color: widget.valueColor),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Bo'lim sarlavhasi — `.sect-h` (11/800 UPPERCASE ls +0.14em).
class DashboardSectionTitle extends StatelessWidget {
  final String title;

  const DashboardSectionTitle(this.title, {super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.s6, bottom: 10),
      child: Text(title.toUpperCase(), style: AppText.sectionLabel),
    );
  }
}

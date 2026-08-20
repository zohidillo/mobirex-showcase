import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/models/dashboard_model.dart';
import '../utils/dashboard_utils.dart';
import '../../../../shared/widgets/app_card.dart';
import 'dashboard_summary_card.dart';

class ComparisonSection extends StatelessWidget {
  final DashboardModel data;
  final String role;

  const ComparisonSection({super.key, required this.data, required this.role});

  bool get _isPhone => role == 'PHONE_SELLER';

  List<_MetricMeta> get _metrics => _isPhone
      ? [
          _MetricMeta('total_sold_value', 'Sotuv'),
          _MetricMeta('phone_profit', 'Telefon foyda'),
          _MetricMeta('net_profit', 'Sof foyda'),
          _MetricMeta('phones_sold_count', 'Sotilgan telefonlar'),
        ]
      : [
          _MetricMeta('total_sold_value', 'Sotuv'),
          _MetricMeta('accessory_profit', 'Aksessuar foyda'),
          _MetricMeta('total_quantity_sold', 'Sotilgan dona'),
          _MetricMeta('total_inventory_value', 'Inventar qiymati'),
        ];

  @override
  Widget build(BuildContext context) {
    final hasPrev = data.previousMonthComparison?.isNotEmpty == true;
    final hasAll = data.allTimeComparison?.isNotEmpty == true;
    if (!hasPrev && !hasAll) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const DashboardSectionTitle('Taqqoslash'),
        if (hasPrev) ...[
          _GroupLabel("O'tgan oyga nisbatan"),
          const SizedBox(height: 8),
          _ComparisonGroup(
            compMap: data.previousMonthComparison!,
            metrics: _metrics,
            showPrevious: true,
          ),
          const SizedBox(height: 16),
        ],
        if (hasAll) ...[
          _GroupLabel("Umumiy davr o'rtachasiga nisbatan"),
          const SizedBox(height: 8),
          _ComparisonGroup(
            compMap: data.allTimeComparison!,
            metrics: _metrics,
            showPrevious: false,
          ),
        ],
      ],
    );
  }
}

class _MetricMeta {
  final String key;
  final String label;
  const _MetricMeta(this.key, this.label);
}

/// `.cmp-h` — 12px/600 `--ink-2`.
class _GroupLabel extends StatelessWidget {
  final String text;
  const _GroupLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        color: AppColors.ink2,
      ),
    );
  }
}

class _ComparisonGroup extends StatelessWidget {
  final Map<String, ComparisonItemModel> compMap;
  final List<_MetricMeta> metrics;
  final bool showPrevious;

  const _ComparisonGroup({
    required this.compMap,
    required this.metrics,
    required this.showPrevious,
  });

  @override
  Widget build(BuildContext context) {
    final visible = metrics.where((m) => compMap.containsKey(m.key)).toList();
    if (visible.isEmpty) return const SizedBox.shrink();

    return Column(
      children: visible.map((m) {
        final item = compMap[m.key]!;
        return Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: _ComparisonCard(
            label: m.label,
            item: item,
            showPrevious: showPrevious,
          ),
        );
      }).toList(),
    );
  }
}

class _ComparisonCard extends StatelessWidget {
  final String label;
  final ComparisonItemModel item;
  final bool showPrevious;

  const _ComparisonCard({
    required this.label,
    required this.item,
    required this.showPrevious,
  });

  @override
  Widget build(BuildContext context) {
    final dir = item.direction;
    final isUp = dir == 'up';
    final isDown = dir == 'down';
    final dirColor = isUp
        ? AppColors.pos
        : isDown
        ? AppColors.neg
        : AppColors.ink3;

    final dirIcon = isUp
        ? Icons.arrow_upward
        : isDown
        ? Icons.arrow_downward
        : null;

    final compareValue = showPrevious ? item.previous : item.average;
    final compareLabel = showPrevious ? "O'tgan oy" : "O'rtacha";

    return AppCard(
      edge: isUp
          ? AppCardEdge.positive
          : isDown
          ? AppCardEdge.negative
          : AppCardEdge.neutral,
      padding: const EdgeInsets.fromLTRB(AppSpacing.s4, 13, AppSpacing.s4, 13),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(fontSize: 12, color: AppColors.ink2),
                ),
                const SizedBox(height: 2),
                Text.rich(
                  TextSpan(
                    text: fmtAmount(item.current),
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: AppColors.ink,
                      fontFeatures: [FontFeature.tabularFigures()],
                    ),
                    children: [
                      if (compareValue != null)
                        TextSpan(
                          text:
                              ' / $compareLabel: ${fmtAmount(compareValue)}',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                            color: AppColors.ink3,
                          ),
                        ),
                    ],
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                if (item.diff != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    _diffLabel(item),
                    style: TextStyle(fontSize: 12, color: dirColor),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.s3),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (dirIcon != null)
                Icon(dirIcon, size: 18, color: dirColor)
              else
                Text(
                  '—',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: dirColor,
                  ),
                ),
              if (item.percent != null) ...[
                const SizedBox(height: 2),
                Text(
                  '${item.percent!.toStringAsFixed(1)}%',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: dirColor,
                  ),
                ),
              ] else if (isUp) ...[
                const SizedBox(height: 2),
                const Text(
                  'Yangi',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: AppColors.pos,
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  String _diffLabel(ComparisonItemModel item) {
    final diff = item.diff;
    if (diff == null) return '';
    final dir = item.direction;
    final prefix = diff > 0 ? '+' : '';
    final suffix = dir == 'up'
        ? ' (Oshgan)'
        : dir == 'down'
        ? ' (Kamaygan)'
        : " (O'zgarish yo'q)";
    return '$prefix${fmtAmount(diff)}$suffix';
  }
}

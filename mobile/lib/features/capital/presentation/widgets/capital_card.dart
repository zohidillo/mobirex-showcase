import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_tag.dart';
import '../../data/models/capital_model.dart';

/// Kapital kartasi — `redesign4/capital/phone-capital.html` `.card.pos`.
///
/// Sarlavha — filial, yonida "Joriy oy" aksent yorlig'i va (ruxsat bo'lsa)
/// ⋮ menyusi. Hero — joriy balans, kichik qo'shimcha "tikilgan $X".
class CapitalCard extends StatelessWidget {
  final CapitalModel capital;
  final bool showActions;
  final VoidCallback? onAddInvestment;
  final VoidCallback? onReset;

  const CapitalCard({
    super.key,
    required this.capital,
    this.showActions = false,
    this.onAddInvestment,
    this.onReset,
  });

  String _formatMonth(DateTime? dt) {
    if (dt == null) return '';
    return DateFormat('MMMM yyyy').format(dt);
  }

  @override
  Widget build(BuildContext context) {
    final isCurrentMonth = capital.isCurrentMonth;
    final branchName = capital.branch?.name ?? '';

    return AppCard(
      edge: AppCardEdge.positive,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  branchName,
                  style: AppText.bodyLg,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (isCurrentMonth) ...[
                const SizedBox(width: 10),
                const AppTag(label: 'Joriy oy', color: AppColors.action),
              ],
              if (showActions && isCurrentMonth)
                PopupMenuButton<String>(
                  icon: const Icon(
                    Icons.more_vert,
                    color: AppColors.ink3,
                    size: 18,
                  ),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 32),
                  onSelected: (value) {
                    if (value == 'reset' && onReset != null) onReset!();
                  },
                  itemBuilder: (_) => [
                    const PopupMenuItem(
                      value: 'reset',
                      child: Row(
                        children: [
                          Icon(Icons.restart_alt, size: 18),
                          SizedBox(width: AppSpacing.s2),
                          Text('Kapitalni nolga tushirish'),
                        ],
                      ),
                    ),
                  ],
                ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: AppHeroValue(
              value: formatMoney(capital.currentBalance),
              suffix: 'tikilgan ${formatMoney(capital.investedAmount)}',
              color: AppColors.pos,
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 7),
            child: Text(
              _formatMonth(capital.month),
              style: AppText.meta,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

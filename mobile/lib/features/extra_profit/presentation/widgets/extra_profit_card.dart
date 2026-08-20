import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_secondary_button.dart';
import '../../../phones/presentation/widgets/phone_card.dart'
    show PhoneCardTitleRow;
import '../../data/models/extra_profit_model.dart';

/// Qo'shimcha foyda kartasi —
/// `redesign4/extra-profit/extra-profit.html` `.card.pos`.
///
/// Sarlavha — izoh (bo'lmasa "Qo'shimcha foyda"), hero — musbat summa,
/// meta — "kiritgan · sana".
class ExtraProfitCard extends StatelessWidget {
  final ExtraProfitModel profit;
  final bool canDelete;
  final VoidCallback? onDelete;

  const ExtraProfitCard({
    super.key,
    required this.profit,
    this.canDelete = false,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final title = (profit.note != null && profit.note!.isNotEmpty)
        ? profit.note!
        : "Qo'shimcha foyda";

    final meta = <String>[
      if (profit.createdBy != null) profit.createdBy!.username,
      formatDate(profit.addedAt),
    ].join(' · ');

    return AppCard(
      edge: AppCardEdge.positive,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          PhoneCardTitleRow(title: title, trailing: profit.branch?.name),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: AppHeroValue(
              value: formatMoney(profit.amount),
              color: AppColors.pos,
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 7),
            child: Text(
              meta,
              style: AppText.meta,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (canDelete && onDelete != null)
            Padding(
              padding: const EdgeInsets.only(top: AppSpacing.s3),
              child: Row(
                children: [
                  const Spacer(),
                  AppSecondaryButton(
                    label: 'O\'chirish',
                    onPressed: onDelete,
                    isDanger: true,
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

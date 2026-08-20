import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_secondary_button.dart';
import '../../../../shared/widgets/app_tag.dart';
import '../../data/models/debt_model.dart';

/// Qarz kartasi — `redesign4/debts/unpaid-debts.html` `.card.pos` / `.card.neg`.
///
/// Chap qirra va hero rangi yo'nalishga bog'liq: WE_GAVE → `--pos`,
/// WE_TOOK → `--neg`. Hero — qoldiq, yonida kichik "jami $X".
class DebtCard extends StatelessWidget {
  final DebtModel debt;
  final bool canPay;
  final bool canDelete;
  final VoidCallback? onTap;
  final VoidCallback? onPay;
  final VoidCallback? onDelete;

  const DebtCard({
    super.key,
    required this.debt,
    this.canPay = false,
    this.canDelete = false,
    this.onTap,
    this.onPay,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final isWeGave = debt.isWeGave;
    final directionColor = isWeGave ? AppColors.pos : AppColors.neg;
    final hasActions =
        (canPay && onPay != null) || (canDelete && onDelete != null);

    final meta = <String>[
      formatDateShort(debt.addedAt),
      if (debt.createdBy != null) debt.createdBy!.username,
      if (debt.branch != null) debt.branch!.name,
    ].join(' · ');

    return AppCard(
      onTap: onTap,
      edge: isWeGave ? AppCardEdge.positive : AppCardEdge.negative,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  debt.fName,
                  style: AppText.bodyLg,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 10),
              AppTag(
                label: debt.directionDisplay.isNotEmpty
                    ? debt.directionDisplay
                    : debt.direction,
                color: directionColor,
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: AppHeroValue(
              value: formatMoney(debt.remainingAmount),
              suffix: 'jami ${formatMoney(debt.amount)}',
              color: directionColor,
            ),
          ),
          if (debt.note != null && debt.note!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 5),
              child: Text(
                debt.note!,
                style: const TextStyle(fontSize: 12.5, color: AppColors.ink2),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
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
          if (hasActions)
            Padding(
              padding: const EdgeInsets.only(top: AppSpacing.s3),
              child: Row(
                children: [
                  const Spacer(),
                  if (canDelete && onDelete != null) ...[
                    AppSecondaryButton(
                      label: 'O\'chirish',
                      onPressed: onDelete,
                      isDanger: true,
                    ),
                    const SizedBox(width: 6),
                  ],
                  if (canPay && onPay != null)
                    AppPrimaryButton(label: 'To\'lash', onPressed: onPay),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

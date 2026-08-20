import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_secondary_button.dart';
import '../../../phones/presentation/widgets/phone_card.dart'
    show PhoneCardTitleRow;
import '../../data/models/expense_model.dart';

/// Xarajat kartasi — `redesign4/expenses/expenses.html` `.card.neg`.
///
/// Sarlavha — izoh (bo'lmasa turi), hero — manfiy summa,
/// meta — "turi · kiritgan · sana".
class ExpenseCard extends StatelessWidget {
  final ExpenseModel expense;
  final bool canDelete;
  final VoidCallback? onDelete;

  const ExpenseCard({
    super.key,
    required this.expense,
    this.canDelete = false,
    this.onDelete,
  });

  String _typeLabel() {
    if (expense.typeDisplay.isNotEmpty) return expense.typeDisplay;
    return switch (expense.type) {
      'SHOP_EXPENSE' => "Do'kon xarajati",
      'EMPLOYEE_EXPENSE' => 'Xodim xarajati',
      _ => expense.type,
    };
  }

  @override
  Widget build(BuildContext context) {
    final title = (expense.note != null && expense.note!.isNotEmpty)
        ? expense.note!
        : _typeLabel();

    final meta = <String>[
      _typeLabel(),
      if (expense.employee != null) expense.employee!.username,
      if (expense.createdBy != null) expense.createdBy!.username,
      formatDate(expense.addedAt),
    ].join(' · ');

    return AppCard(
      edge: AppCardEdge.negative,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          PhoneCardTitleRow(title: title, trailing: expense.branch?.name),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: AppHeroValue(
              value: '-${formatMoney(expense.amount)}',
              color: AppColors.neg,
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

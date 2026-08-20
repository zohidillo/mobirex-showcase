import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_secondary_button.dart';
import '../../../phones/presentation/widgets/phone_card.dart'
    show PhoneCardTitleRow;
import '../../data/models/salary_model.dart';

/// Oylik kartasi — `redesign4/salaries/salaries.html` `.card`.
///
/// Sarlavha — xodim ismi, hero — summa (neytral),
/// ikkinchi qator — izoh, meta — "sana · Kiritgan: admin".
class SalaryCard extends StatelessWidget {
  final SalaryModel salary;
  final bool canDelete;
  final VoidCallback? onDelete;

  const SalaryCard({
    super.key,
    required this.salary,
    this.canDelete = false,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final employee = salary.employee;
    final meta = <String>[
      formatDateShort(salary.addedAt),
      if (salary.createdBy != null) 'Kiritgan: ${salary.createdBy!.username}',
    ].join(' · ');

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          PhoneCardTitleRow(
            title: employee?.displayName ?? 'Unknown',
            trailing: salary.branch?.name,
          ),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: AppHeroValue(value: formatMoney(salary.amount)),
          ),
          if (salary.note != null && salary.note!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 5),
              child: Text(
                salary.note!,
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

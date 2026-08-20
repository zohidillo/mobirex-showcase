import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_secondary_button.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../data/models/debt_model.dart';

/// To'lov dialogi — `redesign4/debts/unpaid-debts.html` (12-frame) + `.dialog`.
///
/// Validatsiya va `onPay` mantig'i o'zgarmadi.
class PayDebtDialog extends StatefulWidget {
  final DebtModel debt;
  final Future<String?> Function(String amount, {String? note}) onPay;

  const PayDebtDialog({super.key, required this.debt, required this.onPay});

  @override
  State<PayDebtDialog> createState() => _PayDebtDialogState();
}

class _PayDebtDialogState extends State<PayDebtDialog> {
  final _amountCtrl = TextEditingController();
  final _noteCtrl = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _amountCtrl.dispose();
    _noteCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final amount = _amountCtrl.text.trim();
    if (amount.isEmpty) {
      setState(() => _error = 'Summa majburiy');
      return;
    }
    final parsed = double.tryParse(amount);
    if (parsed == null || parsed <= 0) {
      setState(() => _error = 'To\'g\'ri summa kiriting');
      return;
    }
    final remaining = double.tryParse(widget.debt.remainingAmount) ?? 0;
    if (parsed > remaining) {
      setState(() => _error = 'Summa qolgan qarzdan ko\'p');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    final note = _noteCtrl.text.trim();
    final err = await widget.onPay(amount, note: note.isNotEmpty ? note : null);

    if (mounted) {
      if (err != null) {
        setState(() {
          _error = parseApiError(err);
          _loading = false;
        });
      } else {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('To\'lov qayd etildi'),
            backgroundColor: AppColors.pos,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      insetPadding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s6,
        vertical: AppSpacing.s6,
      ),
      titlePadding: const EdgeInsets.fromLTRB(22, 22, 22, 0),
      contentPadding: const EdgeInsets.fromLTRB(22, 10, 22, 0),
      actionsPadding: const EdgeInsets.fromLTRB(22, 18, 22, 14),
      title: Text('To\'lov — ${widget.debt.fName}'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (_error != null) ...[
            InlineError(message: _error!),
            const SizedBox(height: AppSpacing.s3),
          ],
          Text.rich(
            TextSpan(
              text: 'Qoldiq: ',
              style: const TextStyle(fontSize: 14, color: AppColors.ink2),
              children: [
                TextSpan(
                  text: formatMoney(widget.debt.remainingAmount),
                  style: const TextStyle(
                    color: AppColors.ink,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.s4),
          AppTextField(
            label: 'To\'lov summasi',
            controller: _amountCtrl,
            autofocus: true,
            prefixText: '\$ ',
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: AppSpacing.s3),
          AppTextField(label: 'Izoh (ixtiyoriy)', controller: _noteCtrl),
        ],
      ),
      actions: [
        AppSecondaryButton(
          label: 'Bekor qilish',
          onPressed: () => Navigator.of(context).pop(),
        ),
        const SizedBox(width: 6),
        AppPrimaryButton(
          label: 'To\'lash',
          isLoading: _loading,
          onPressed: _loading ? null : _submit,
        ),
      ],
    );
  }
}

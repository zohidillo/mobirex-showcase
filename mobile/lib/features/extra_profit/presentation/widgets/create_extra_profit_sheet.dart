import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';

class CreateExtraProfitSheet extends StatefulWidget {
  final Future<String?> Function({required String amount, String? note})
  onCreate;

  const CreateExtraProfitSheet({super.key, required this.onCreate});

  @override
  State<CreateExtraProfitSheet> createState() => _CreateExtraProfitSheetState();
}

class _CreateExtraProfitSheetState extends State<CreateExtraProfitSheet> {
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
    if (double.tryParse(amount) == null) {
      setState(() => _error = 'To\'g\'ri summa kiriting');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    final err = await widget.onCreate(
      amount: amount,
      note: _noteCtrl.text.trim().isNotEmpty ? _noteCtrl.text.trim() : null,
    );
    if (mounted) {
      if (err != null) {
        setState(() {
          _error = parseApiError(err);
          _loading = false;
        });
      } else {
        Navigator.of(context).pop();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        AppSpacing.s6,
        14,
        AppSpacing.s6,
        MediaQuery.of(context).viewInsets.bottom + AppSpacing.s6,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const AppSheetHandle(),
          const Text(
            "Qo'shimcha foyda qo'shish",
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.ink,
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.s4),
            InlineError(message: _error!),
          ],
          const SizedBox(height: AppSpacing.s4),
          AppTextField(
            label: 'Summa',
            controller: _amountCtrl,
            autofocus: true,
            prefixText: '\$ ',
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: AppSpacing.s4),
          AppTextField(
            label: 'Izoh (ixtiyoriy)',
            controller: _noteCtrl,
            maxLines: 2,
          ),
          const SizedBox(height: AppSpacing.s5),
          AppPrimaryButton(
            label: 'Saqlash',
            block: true,
            isLoading: _loading,
            onPressed: _loading ? null : _submit,
          ),
        ],
      ),
    );
  }
}

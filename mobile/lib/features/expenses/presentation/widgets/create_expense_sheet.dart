import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';

// Expense type choices as defined by the backend serializer.
// Add more entries here when the backend exposes additional types.
const _kExpenseTypes = [
  (value: 'SHOP_EXPENSE', label: "Do'kon xarajati"),
  (value: 'EMPLOYEE_EXPENSE', label: "Xodim xarajati"),
];

class CreateExpenseSheet extends StatefulWidget {
  final Future<String?> Function({
    required String type,
    required String amount,
    String? note,
  })
  onCreate;

  const CreateExpenseSheet({super.key, required this.onCreate});

  @override
  State<CreateExpenseSheet> createState() => _CreateExpenseSheetState();
}

class _CreateExpenseSheetState extends State<CreateExpenseSheet> {
  String? _selectedType = 'SHOP_EXPENSE';
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
    if (_selectedType == null) {
      setState(() => _error = 'Xarajat turini tanlang');
      return;
    }
    final amount = _amountCtrl.text.trim();
    if (amount.isEmpty) {
      setState(() => _error = 'Summa kiritilishi shart');
      return;
    }
    final parsed = double.tryParse(amount);
    if (parsed == null || parsed <= 0) {
      setState(() => _error = "To'g'ri summa kiriting");
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    final note = _noteCtrl.text.trim();
    final err = await widget.onCreate(
      type: _selectedType!,
      amount: amount,
      note: note.isNotEmpty ? note : null,
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
            "Xarajat qo'shish",
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
          AppSelectField<String>(
            label: 'Xarajat turi',
            sheetTitle: 'Xarajat turi',
            hint: 'Turini tanlang',
            value: _selectedType,
            options: _kExpenseTypes
                .map((t) => AppSelectOption(value: t.value, label: t.label))
                .toList(),
            onChanged: (v) => setState(() => _selectedType = v),
          ),
          const SizedBox(height: AppSpacing.s4),
          AppTextField(
            label: 'Summa',
            controller: _amountCtrl,
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

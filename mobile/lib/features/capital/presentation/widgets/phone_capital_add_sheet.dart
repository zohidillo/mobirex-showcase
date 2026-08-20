import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../features/profile/data/models/user_model.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';

class PhoneCapitalAddSheet extends StatefulWidget {
  final List<UserBranch> branches;
  final Future<String?> Function({
    required int branchId,
    required String amount,
  })
  onAdd;

  const PhoneCapitalAddSheet({
    super.key,
    required this.branches,
    required this.onAdd,
  });

  @override
  State<PhoneCapitalAddSheet> createState() => _PhoneCapitalAddSheetState();
}

class _PhoneCapitalAddSheetState extends State<PhoneCapitalAddSheet> {
  int? _selectedBranchId;
  final _amountCtrl = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    if (widget.branches.length == 1) {
      _selectedBranchId = widget.branches.first.id;
    }
  }

  @override
  void dispose() {
    _amountCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_selectedBranchId == null) {
      setState(() => _error = 'Filialni tanlang');
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
    final err = await widget.onAdd(
      branchId: _selectedBranchId!,
      amount: amount,
    );
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
            content: Text("Kapital muvaffaqiyatli qo'shildi"),
            backgroundColor: AppColors.pos,
          ),
        );
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
            "Telefon kapital qo'shish",
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
          AppSelectField<int>(
            label: 'Filial',
            sheetTitle: 'Filialni tanlang',
            hint: 'Filialni tanlang',
            value: _selectedBranchId,
            options: widget.branches
                .map((b) => AppSelectOption(value: b.id, label: b.name))
                .toList(),
            onChanged: (v) => setState(() => _selectedBranchId = v),
          ),
          const SizedBox(height: AppSpacing.s4),
          AppTextField(
            label: 'Summa',
            controller: _amountCtrl,
            prefixText: r'$ ',
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: AppSpacing.s5),
          AppPrimaryButton(
            label: "Qo'shish",
            block: true,
            isLoading: _loading,
            onPressed: _loading ? null : _submit,
          ),
        ],
      ),
    );
  }
}

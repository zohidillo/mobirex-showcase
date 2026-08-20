import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_section_label.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';

/// Qarz qo'shish varag'i — `redesign4/debts/unpaid-debts.html` (9-11 frame).
///
/// Mantiq (validatsiya, `onCreate`, yo'nalish qiymatlari) o'zgarmadi.
class CreateDebtSheet extends StatefulWidget {
  final Future<String?> Function({
    required String fName,
    required String amount,
    required String direction,
    String? note,
  })
  onCreate;

  const CreateDebtSheet({super.key, required this.onCreate});

  @override
  State<CreateDebtSheet> createState() => _CreateDebtSheetState();
}

class _CreateDebtSheetState extends State<CreateDebtSheet> {
  final _fNameCtrl = TextEditingController();
  final _amountCtrl = TextEditingController();
  final _noteCtrl = TextEditingController();
  String _direction = 'WE_GAVE';
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _fNameCtrl.dispose();
    _amountCtrl.dispose();
    _noteCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final fName = _fNameCtrl.text.trim();
    final amount = _amountCtrl.text.trim();

    if (fName.isEmpty) {
      setState(() => _error = 'Ism yoki kompaniya nomi majburiy');
      return;
    }
    if (amount.isEmpty) {
      setState(() => _error = 'Summa majburiy');
      return;
    }
    final parsed = double.tryParse(amount);
    if (parsed == null || parsed <= 0) {
      setState(() => _error = 'To\'g\'ri summa kiriting');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    final err = await widget.onCreate(
      fName: fName,
      amount: amount,
      direction: _direction,
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
            'Qarz qo\'shish',
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
            label: 'Ism yoki kompaniya',
            controller: _fNameCtrl,
            textCapitalization: TextCapitalization.words,
          ),
          const SizedBox(height: AppSpacing.s4),
          AppTextField(
            label: 'Summa',
            controller: _amountCtrl,
            prefixText: '\$ ',
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
          ),
          const SizedBox(height: AppSpacing.s4),
          const AppFieldLabel('Yo\'nalish'),
          Row(
            children: [
              _DirectionChip(
                label: 'Biz berdik',
                selected: _direction == 'WE_GAVE',
                onTap: () => setState(() => _direction = 'WE_GAVE'),
              ),
              const SizedBox(width: AppSpacing.s2),
              _DirectionChip(
                label: 'Biz oldik',
                selected: _direction == 'WE_TOOK',
                onTap: () => setState(() => _direction = 'WE_TOOK'),
              ),
            ],
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

/// Yo'nalish segmenti — `.fdrop` / `.fdrop.set` (tanlanganda aksent).
class _DirectionChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _DirectionChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          onTap: onTap,
          borderRadius: AppRadius.chipRadius,
          child: AnimatedContainer(
            duration: AppDurations.press,
            curve: AppCurves.press,
            height: 38,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: AppRadius.chipRadius,
              border: Border.all(
                color: selected ? AppColors.action : Colors.transparent,
              ),
            ),
            child: Text(
              label,
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
                color: selected ? AppColors.action : AppColors.ink3,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

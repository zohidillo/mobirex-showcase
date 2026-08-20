import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_section_label.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../profile/data/models/user_model.dart';
import '../providers/salary_provider.dart';

class CreateSalarySheet extends ConsumerStatefulWidget {
  final List<UserBranch> branches;
  final Future<String?> Function({
    required int employeeId,
    required String amount,
    String? note,
  })
  onCreate;

  const CreateSalarySheet({
    super.key,
    required this.branches,
    required this.onCreate,
  });

  @override
  ConsumerState<CreateSalarySheet> createState() => _CreateSalarySheetState();
}

class _CreateSalarySheetState extends ConsumerState<CreateSalarySheet> {
  int? _selectedBranchId;
  int? _selectedEmployeeId;
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
    if (_selectedEmployeeId == null) {
      setState(() => _error = 'Xodimni tanlang');
      return;
    }
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
      employeeId: _selectedEmployeeId!,
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
    final staffAsync = ref.watch(staffListProvider(_selectedBranchId));

    return Padding(
      padding: EdgeInsets.fromLTRB(
        AppSpacing.s6,
        14,
        AppSpacing.s6,
        MediaQuery.of(context).viewInsets.bottom + AppSpacing.s6,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const AppSheetHandle(),
            const Text(
              'Oylik to\'lash',
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
            if (widget.branches.isNotEmpty) ...[
              AppSelectField<int?>(
                label: 'Filial',
                sheetTitle: 'Filial',
                hint: 'Barcha filiallar',
                value: _selectedBranchId,
                options: [
                  const AppSelectOption(
                    value: null,
                    label: 'Barcha filiallar',
                  ),
                  ...widget.branches.map(
                    (b) => AppSelectOption<int?>(value: b.id, label: b.name),
                  ),
                ],
                onChanged: (v) {
                  setState(() {
                    _selectedBranchId = v;
                    _selectedEmployeeId = null;
                  });
                  ref.invalidate(staffListProvider(v));
                },
              ),
              const SizedBox(height: AppSpacing.s4),
            ],
            staffAsync.when(
              loading: () => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  AppFieldLabel('Xodim'),
                  LinearProgressIndicator(),
                ],
              ),
              error: (e, _) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const AppFieldLabel('Xodim'),
                  Text(
                    parseApiError(e),
                    style: const TextStyle(color: AppColors.neg, fontSize: 13),
                  ),
                ],
              ),
              data: (staff) {
                if (staff.isEmpty) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      AppFieldLabel('Xodim'),
                      Text(
                        'Xodimlar topilmadi',
                        style: TextStyle(color: AppColors.ink3, fontSize: 13),
                      ),
                    ],
                  );
                }
                return AppSelectField<int?>(
                  label: 'Xodim',
                  sheetTitle: 'Xodimni tanlang',
                  hint: 'Xodimni tanlang',
                  value: _selectedEmployeeId,
                  options: staff
                      .map(
                        (s) => AppSelectOption<int?>(
                          value: s.id,
                          label: '${s.displayName} (${s.role})',
                        ),
                      )
                      .toList(),
                  onChanged: (v) => setState(() => _selectedEmployeeId = v),
                );
              },
            ),
            const SizedBox(height: AppSpacing.s4),
            AppTextField(
              label: 'Summa',
              controller: _amountCtrl,
              prefixText: '\$ ',
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
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
      ),
    );
  }
}

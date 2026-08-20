import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/router/navigation_helper.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../../shared/providers/category_provider.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/phone_provider.dart';

const _storageChoices = [
  ('16', '16 GB'),
  ('32', '32 GB'),
  ('64', '64 GB'),
  ('128', '128 GB'),
  ('256', '256 GB'),
  ('512', '512 GB'),
  ('1024', '1 TB'),
  ('2048', '2 TB'),
];

class AddPhonePage extends ConsumerStatefulWidget {
  const AddPhonePage({super.key});

  @override
  ConsumerState<AddPhonePage> createState() => _AddPhonePageState();
}

class _AddPhonePageState extends ConsumerState<AddPhonePage> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _imeiCtrl = TextEditingController();
  final _colorCtrl = TextEditingController();
  final _costCtrl = TextEditingController();
  final _fromCtrl = TextEditingController();

  int? _selectedBranchId;
  int? _selectedCategoryId;
  String? _selectedStorage;
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _imeiCtrl.dispose();
    _colorCtrl.dispose();
    _costCtrl.dispose();
    _fromCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedBranchId == null) {
      setState(() => _error = 'Filialni tanlang');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    final data = <String, dynamic>{
      'name': _nameCtrl.text.trim(),
      'imei': _imeiCtrl.text.trim(),
      'color': _colorCtrl.text.trim(),
      'cost_price': _costCtrl.text.trim(),
      'from_by': _fromCtrl.text.trim(),
      'branch': _selectedBranchId,
    };
    if (_selectedStorage != null) {
      data['storage'] = _selectedStorage;
    }
    if (_selectedCategoryId != null) {
      data['category'] = _selectedCategoryId;
    }

    try {
      await ref.read(phoneRepositoryProvider).createPhone(data);
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = parseApiError(e);
          _isLoading = false;
        });
      }
      return;
    }

    ref.invalidate(unsoldPhonesProvider);

    if (!mounted) return;
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/phones/unsold');
    }
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Telefon muvaffaqiyatli qo\'shildi'),
        backgroundColor: AppColors.pos,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authProvider).user;
    final branches = user?.branches ?? [];
    final catState = ref.watch(phoneCategoriesProvider);

    if (branches.length == 1 && _selectedBranchId == null) {
      _selectedBranchId = branches.first.id;
    }

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Telefon qo\'shish',
        onBack: () => goBack(context, ref),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.s4,
            AppSpacing.s4,
            AppSpacing.s4,
            AppSpacing.s8,
          ),
          children: [
            if (_error != null) ...[
              InlineError(message: _error!),
              const SizedBox(height: AppSpacing.s4),
            ],
            AppTextField(
              label: 'Telefon nomi *',
              controller: _nameCtrl,
              textInputAction: TextInputAction.next,
              validator: (v) =>
                  v == null || v.trim().isEmpty ? 'Majburiy' : null,
            ),
            const SizedBox(height: AppSpacing.s4),
            AppTextField(
              label: 'IMEI *',
              controller: _imeiCtrl,
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.next,
              validator: (v) =>
                  v == null || v.trim().isEmpty ? 'IMEI kiritish shart' : null,
            ),
            const SizedBox(height: AppSpacing.s4),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: AppSelectField<String?>(
                    label: 'Xotira *',
                    sheetTitle: 'Xotira',
                    value: _selectedStorage,
                    options: [
                      const AppSelectOption(value: null, label: '—'),
                      ..._storageChoices.map(
                        (c) => AppSelectOption(value: c.$1, label: c.$2),
                      ),
                    ],
                    onChanged: (v) => setState(() => _selectedStorage = v),
                    validator: (v) =>
                        v == null ? 'Xotira hajmini tanlang' : null,
                  ),
                ),
                const SizedBox(width: AppSpacing.s3),
                Expanded(
                  child: AppTextField(
                    label: 'Rang',
                    controller: _colorCtrl,
                    textInputAction: TextInputAction.next,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.s4),
            AppTextField(
              label: 'Narx *',
              controller: _costCtrl,
              prefixText: '\$ ',
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              textInputAction: TextInputAction.next,
              validator: (v) =>
                  v == null || v.trim().isEmpty ? 'Majburiy' : null,
            ),
            const SizedBox(height: AppSpacing.s4),
            AppTextField(
              label: 'Qayerdan olingan *',
              controller: _fromCtrl,
              textInputAction: TextInputAction.next,
              validator: (v) => v == null || v.trim().isEmpty
                  ? 'Qayerdan olinganini kiriting'
                  : null,
            ),
            const SizedBox(height: AppSpacing.s4),
            AppSelectField<int>(
              label: 'Filial *',
              sheetTitle: 'Filial',
              value: _selectedBranchId,
              options: branches
                  .map((b) => AppSelectOption(value: b.id, label: b.name))
                  .toList(),
              onChanged: (v) => setState(() => _selectedBranchId = v),
              validator: (v) => v == null ? 'Majburiy' : null,
            ),
            const SizedBox(height: AppSpacing.s4),
            _CategoryField(
              catState: catState,
              selectedId: _selectedCategoryId,
              onChanged: (v) => setState(() => _selectedCategoryId = v),
              onRetry: () =>
                  ref.read(phoneCategoriesProvider.notifier).reload(),
            ),
            const SizedBox(height: AppSpacing.s6),
            AppPrimaryButton(
              label: 'Qo\'shish',
              block: true,
              isLoading: _isLoading,
              onPressed: _isLoading ? null : _submit,
            ),
          ],
        ),
      ),
    );
  }
}

class _CategoryField extends StatelessWidget {
  final CategoryState catState;
  final int? selectedId;
  final void Function(int?) onChanged;
  final VoidCallback onRetry;

  const _CategoryField({
    required this.catState,
    required this.selectedId,
    required this.onChanged,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    if (catState.isLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: AppSpacing.s2),
        child: Row(
          children: [
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: AppSpacing.s2),
            Text(
              'Kategoriyalar yuklanmoqda...',
              style: TextStyle(color: AppColors.ink3, fontSize: 13),
            ),
          ],
        ),
      );
    }
    if (catState.error != null && catState.categories.isEmpty) {
      return Row(
        children: [
          const Text(
            'Kategoriyalar yuklanmadi',
            style: TextStyle(color: AppColors.neg, fontSize: 13),
          ),
          TextButton(onPressed: onRetry, child: const Text('Qayta')),
        ],
      );
    }
    if (catState.categories.isEmpty) {
      return const Text(
        'Kategoriyalar topilmadi',
        style: TextStyle(color: AppColors.ink3, fontSize: 13),
      );
    }
    return AppSelectField<int?>(
      label: 'Kategoriya',
      sheetTitle: 'Kategoriya',
      value: selectedId,
      options: [
        const AppSelectOption(value: null, label: '—'),
        ...catState.categories.map(
          (c) => AppSelectOption(value: c.id, label: c.name),
        ),
      ],
      onChanged: onChanged,
    );
  }
}

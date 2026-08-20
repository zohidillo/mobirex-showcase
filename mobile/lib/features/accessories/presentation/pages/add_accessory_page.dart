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
import '../providers/accessory_provider.dart';

class AddAccessoryPage extends ConsumerStatefulWidget {
  const AddAccessoryPage({super.key});

  @override
  ConsumerState<AddAccessoryPage> createState() => _AddAccessoryPageState();
}

class _AddAccessoryPageState extends ConsumerState<AddAccessoryPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _unitCostCtrl = TextEditingController();
  final _stockCtrl = TextEditingController(text: '1');

  int? _selectedBranchId;
  int? _selectedCategoryId;
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _unitCostCtrl.dispose();
    _stockCtrl.dispose();
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
      'unit_cost': _unitCostCtrl.text.trim(),
      'stock': int.tryParse(_stockCtrl.text.trim()) ?? 1,
      'branch': _selectedBranchId,
    };
    if (_selectedCategoryId != null) {
      data['category'] = _selectedCategoryId;
    }

    try {
      await ref.read(accessoryRepositoryProvider).createAccessory(data);
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = parseApiError(e);
          _isLoading = false;
        });
      }
      return;
    }

    await ref.read(unsoldAccessoriesProvider.notifier).load(refresh: true);

    if (!mounted) return;
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/accessories/unsold');
    }
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Aksessuar muvaffaqiyatli qo\'shildi'),
        backgroundColor: AppColors.pos,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authProvider).user;
    final branches = user?.branches ?? [];
    final catState = ref.watch(accessoryCategoriesProvider);

    if (branches.length == 1 && _selectedBranchId == null) {
      _selectedBranchId = branches.first.id;
    }

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Aksessuar qo\'shish',
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
              label: 'Aksessuar nomi *',
              controller: _nameCtrl,
              textInputAction: TextInputAction.next,
              validator: (v) =>
                  v == null || v.trim().isEmpty ? 'Majburiy' : null,
            ),
            const SizedBox(height: AppSpacing.s4),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: AppTextField(
                    label: 'Narx *',
                    controller: _unitCostCtrl,
                    prefixText: '\$ ',
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    textInputAction: TextInputAction.next,
                    validator: (v) =>
                        v == null || v.trim().isEmpty ? 'Majburiy' : null,
                  ),
                ),
                const SizedBox(width: AppSpacing.s3),
                Expanded(
                  child: AppTextField(
                    label: 'Miqdor *',
                    controller: _stockCtrl,
                    keyboardType: TextInputType.number,
                    textInputAction: TextInputAction.next,
                    validator: (v) {
                      if (v == null || v.trim().isEmpty) return 'Majburiy';
                      if (int.tryParse(v) == null) return 'Raqam kiriting';
                      return null;
                    },
                  ),
                ),
              ],
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
                  ref.read(accessoryCategoriesProvider.notifier).reload(),
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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/app_danger_button.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../profile/data/models/user_model.dart';
import '../providers/support_provider.dart';

class AccountDeleteForm extends ConsumerStatefulWidget {
  final UserModel user;
  final VoidCallback onSuccess;

  const AccountDeleteForm({
    super.key,
    required this.user,
    required this.onSuccess,
  });

  @override
  ConsumerState<AccountDeleteForm> createState() => _AccountDeleteFormState();
}

class _AccountDeleteFormState extends ConsumerState<AccountDeleteForm> {
  final _phoneCtrl = TextEditingController();
  final _reasonCtrl = TextEditingController();
  bool _isSubmitting = false;
  String? _error;

  @override
  void dispose() {
    _phoneCtrl.dispose();
    _reasonCtrl.dispose();
    super.dispose();
  }

  String _buildMessage() {
    final user = widget.user;
    final reason = _reasonCtrl.text.trim();
    final branchSummary = user.branches.isNotEmpty
        ? user.branches.map((b) => '${b.name} (${b.role})').join(', ')
        : "Yo'q";

    return "Accountni o'chirish so'rovi.\n\n"
        "Foydalanuvchi:\n"
        "ID: ${user.id}\n"
        "Username: ${user.username}\n"
        "Ism: ${user.firstName}\n"
        "Familiya: ${user.lastName}\n"
        "Telefon: ${user.phone.isNotEmpty ? user.phone : "Ko'rsatilmagan"}\n"
        "Rollar/filiallar: $branchSummary\n\n"
        "Sabab:\n"
        "${reason.isNotEmpty ? reason : "Ko'rsatilmagan"}";
  }

  Future<void> _submit() async {
    final phone = _phoneCtrl.text.trim();
    if (phone.isEmpty) {
      setState(() => _error = 'Telefon raqam kiritilishi shart');
      return;
    }

    setState(() {
      _isSubmitting = true;
      _error = null;
    });

    try {
      await ref
          .read(supportRepositoryProvider)
          .createRequest(
            requestType: 'ACCOUNT_DELETE',
            source: 'MOBILE_APP',
            phone: phone,
            message: _buildMessage(),
          );
      ref.read(supportListProvider.notifier).load(refresh: true);
      if (mounted) {
        setState(() => _isSubmitting = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              "So'rovingiz yuborildi. Tez orada siz bilan bog'lanamiz.",
            ),
            backgroundColor: AppColors.pos,
          ),
        );
        widget.onSuccess();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
          _error = parseApiError(e);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppTextField(
          label: 'Telefon raqam',
          controller: _phoneCtrl,
          keyboardType: TextInputType.phone,
        ),
        const SizedBox(height: AppSpacing.s4),
        AppTextField(
          label: 'Sabab',
          controller: _reasonCtrl,
          maxLines: 4,
          hint: 'Xohlasangiz sababini qisqacha yozing',
        ),
        if (_error != null) ...[
          const SizedBox(height: AppSpacing.s3),
          InlineError(message: _error!),
        ],
        const SizedBox(height: AppSpacing.s5),
        AppDangerButton(
          label: "So'rov yuborish",
          block: true,
          isLoading: _isSubmitting,
          onPressed: _isSubmitting ? null : _submit,
        ),
      ],
    );
  }
}

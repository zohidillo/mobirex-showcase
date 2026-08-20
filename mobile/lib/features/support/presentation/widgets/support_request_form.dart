import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/utils/error_parser.dart';
import '../providers/support_provider.dart';

class SupportRequestForm extends ConsumerStatefulWidget {
  const SupportRequestForm({super.key});

  @override
  ConsumerState<SupportRequestForm> createState() => _SupportRequestFormState();
}

class _SupportRequestFormState extends ConsumerState<SupportRequestForm> {
  final _phoneCtrl = TextEditingController();
  final _messageCtrl = TextEditingController();
  String _requestType = 'CONTACT';
  bool _isSubmitting = false;
  String? _error;

  @override
  void dispose() {
    _phoneCtrl.dispose();
    _messageCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final phone = _phoneCtrl.text.trim();
    final message = _messageCtrl.text.trim();

    if (phone.isEmpty) {
      setState(() => _error = 'Telefon raqam kiritilishi shart');
      return;
    }
    if (message.isEmpty) {
      setState(() => _error = 'Xabar kiritilishi shart');
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
            requestType: _requestType,
            source: 'MOBILE_APP',
            phone: phone,
            message: message,
          );
      ref.read(supportListProvider.notifier).load(refresh: true);
      if (mounted) {
        setState(() => _isSubmitting = false);
        _phoneCtrl.clear();
        _messageCtrl.clear();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              "So'rovingiz yuborildi. Tez orada siz bilan bog'lanamiz.",
            ),
            backgroundColor: AppColors.pos,
          ),
        );
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
        AppSelectField<String>(
          label: 'Murojaat turi',
          sheetTitle: 'Murojaat turi',
          value: _requestType,
          options: const [
            AppSelectOption(value: 'CONTACT', label: 'Murojaat'),
            AppSelectOption(value: 'TECHNICAL', label: 'Texnik masala'),
          ],
          onChanged: (val) {
            if (val != null) setState(() => _requestType = val);
          },
        ),
        const SizedBox(height: AppSpacing.s4),
        AppTextField(
          label: 'Telefon raqam',
          controller: _phoneCtrl,
          keyboardType: TextInputType.phone,
        ),
        const SizedBox(height: AppSpacing.s4),
        AppTextField(
          label: 'Xabar',
          controller: _messageCtrl,
          maxLines: 4,
          hint: 'Savolingiz yoki muammoingizni yozing',
        ),
        if (_error != null) ...[
          const SizedBox(height: AppSpacing.s3),
          InlineError(message: _error!),
        ],
        const SizedBox(height: AppSpacing.s5),
        AppPrimaryButton(
          label: 'Yuborish',
          block: true,
          isLoading: _isSubmitting,
          onPressed: _isSubmitting ? null : _submit,
        ),
      ],
    );
  }
}

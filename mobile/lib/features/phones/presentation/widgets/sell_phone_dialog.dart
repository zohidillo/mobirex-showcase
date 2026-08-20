import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../data/models/phone_model.dart';

/// Sotish varag'i — `redesign4/components.html` "Bottom sheet" bo'limi.
///
/// Tutqich · sarlavha (18/750) · yordamchi qator · input · to'liq kenglikdagi
/// tugma. Mantiq (validatsiya, `onSell`, xato ko'rsatish) o'zgarmadi.
class SellPhoneSheet extends StatefulWidget {
  final PhoneModel phone;
  final Future<String?> Function(String sellPrice) onSell;

  const SellPhoneSheet({super.key, required this.phone, required this.onSell});

  @override
  State<SellPhoneSheet> createState() => _SellPhoneSheetState();
}

class _SellPhoneSheetState extends State<SellPhoneSheet> {
  final _priceCtrl = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _priceCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final price = _priceCtrl.text.trim();
    if (price.isEmpty) {
      setState(() => _error = 'Sotish narxini kiriting');
      return;
    }
    setState(() {
      _isLoading = true;
      _error = null;
    });
    final err = await widget.onSell(price);
    if (mounted) {
      if (err == null) {
        Navigator.pop(context);
      } else {
        setState(() {
          _error = err;
          _isLoading = false;
        });
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
        MediaQuery.viewInsetsOf(context).bottom + AppSpacing.s6,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const AppSheetHandle(),
          Text(
            '${widget.phone.name} — Sotish',
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.ink,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Narx: ${formatMoney(widget.phone.costPrice)}',
            style: const TextStyle(color: AppColors.ink3, fontSize: 13),
          ),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.s4),
            InlineError(message: _error!),
          ],
          const SizedBox(height: AppSpacing.s4),
          AppTextField(
            label: 'Sotish narxi',
            controller: _priceCtrl,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            prefixText: '\$ ',
            autofocus: true,
          ),
          const SizedBox(height: AppSpacing.s5),
          AppPrimaryButton(
            label: 'Sotishni tasdiqlash',
            block: true,
            isLoading: _isLoading,
            onPressed: _isLoading ? null : _submit,
          ),
        ],
      ),
    );
  }
}

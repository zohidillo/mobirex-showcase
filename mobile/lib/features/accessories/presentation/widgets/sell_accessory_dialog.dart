import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../data/models/accessory_model.dart';

/// Aksessuar sotish varag'i — `redesign4/components.html` "Bottom sheet".
///
/// Mantiq (miqdor/ombor validatsiyasi, `onSell`) o'zgarmadi.
class SellAccessorySheet extends StatefulWidget {
  final AccessoryModel accessory;
  final Future<String?> Function(int quantity, String totalPrice) onSell;

  const SellAccessorySheet({
    super.key,
    required this.accessory,
    required this.onSell,
  });

  @override
  State<SellAccessorySheet> createState() => _SellAccessorySheetState();
}

class _SellAccessorySheetState extends State<SellAccessorySheet> {
  final _quantityCtrl = TextEditingController(text: '1');
  final _totalPriceCtrl = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _quantityCtrl.dispose();
    _totalPriceCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final qty = int.tryParse(_quantityCtrl.text.trim());
    final price = _totalPriceCtrl.text.trim();

    if (qty == null || qty < 1) {
      setState(() => _error = 'Miqdorni to\'g\'ri kiriting');
      return;
    }
    if (qty > widget.accessory.stock) {
      setState(
        () =>
            _error = 'Omborda yetarli emas (mavjud: ${widget.accessory.stock})',
      );
      return;
    }
    if (price.isEmpty) {
      setState(() => _error = 'Umumiy narxni kiriting');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    final err = await widget.onSell(qty, price);
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
            '${widget.accessory.name} — Sotish',
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.ink,
            ),
          ),
          const SizedBox(height: AppSpacing.s1),
          Text(
            'Ombor: ${widget.accessory.stock}  •  Narx: ${formatMoney(widget.accessory.unitCost)}',
            style: const TextStyle(color: AppColors.ink3, fontSize: 13),
          ),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.s4),
            InlineError(message: _error!),
          ],
          const SizedBox(height: AppSpacing.s4),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: AppTextField(
                  label: 'Miqdor',
                  controller: _quantityCtrl,
                  keyboardType: TextInputType.number,
                  autofocus: true,
                ),
              ),
              const SizedBox(width: AppSpacing.s3),
              Expanded(
                child: AppTextField(
                  label: 'Umumiy narx',
                  controller: _totalPriceCtrl,
                  prefixText: '\$ ',
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                ),
              ),
            ],
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

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/theme/app_theme.dart';
import 'app_section_label.dart';

/// Input — `tokens.css` `.inp` (+ `.f label`, `.ferr`).
///
/// 52px balandlik · `--card` fon · 1.5px shaffof chegara · 10px radius.
/// Fokus — `--action` chegara, xato — `--neg` chegara, disabled — opacity .45.
///
/// Bu faqat KO'RINISH qobig'i: `controller`, `validator`, `keyboardType`,
/// `inputFormatters` va boshqalar `TextFormField` ga o'zgarishsiz uzatiladi.
class AppTextField extends StatelessWidget {
  const AppTextField({
    super.key,
    this.label,
    this.hint,
    this.controller,
    this.initialValue,
    this.validator,
    this.onChanged,
    this.onFieldSubmitted,
    this.onTap,
    this.keyboardType,
    this.textInputAction,
    this.inputFormatters,
    this.obscureText = false,
    this.enabled = true,
    this.readOnly = false,
    this.autofocus = false,
    this.maxLines = 1,
    this.minLines,
    this.maxLength,
    this.prefixIcon,
    this.suffixIcon,
    this.prefixText,
    this.focusNode,
    this.autovalidateMode,
    this.textCapitalization = TextCapitalization.none,
  });

  final String? label;
  final String? hint;
  final TextEditingController? controller;
  final String? initialValue;
  final String? Function(String?)? validator;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onFieldSubmitted;
  final VoidCallback? onTap;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final List<TextInputFormatter>? inputFormatters;
  final bool obscureText;
  final bool enabled;
  final bool readOnly;
  final bool autofocus;
  final int? maxLines;
  final int? minLines;
  final int? maxLength;
  final IconData? prefixIcon;
  final Widget? suffixIcon;
  final String? prefixText;
  final FocusNode? focusNode;
  final AutovalidateMode? autovalidateMode;
  final TextCapitalization textCapitalization;

  @override
  Widget build(BuildContext context) {
    final field = TextFormField(
      controller: controller,
      initialValue: initialValue,
      validator: validator,
      onChanged: onChanged,
      onFieldSubmitted: onFieldSubmitted,
      onTap: onTap,
      keyboardType: keyboardType,
      textInputAction: textInputAction,
      inputFormatters: inputFormatters,
      obscureText: obscureText,
      enabled: enabled,
      readOnly: readOnly,
      autofocus: autofocus,
      maxLines: obscureText ? 1 : maxLines,
      minLines: minLines,
      maxLength: maxLength,
      focusNode: focusNode,
      autovalidateMode: autovalidateMode,
      textCapitalization: textCapitalization,
      style: AppText.input,
      cursorColor: AppColors.action,
      decoration: InputDecoration(
        hintText: hint,
        prefixText: prefixText,
        prefixIcon: prefixIcon == null
            ? null
            : Icon(prefixIcon, size: 18, color: AppColors.ink3),
        prefixIconConstraints: const BoxConstraints(minWidth: 44),
        suffixIcon: suffixIcon,
        // Balandlik `.inp` = 52px: 15px matn + 2×15 padding + 1.5×2 chegara.
        contentPadding: EdgeInsets.symmetric(
          horizontal: prefixIcon == null ? 15 : 0,
          vertical: maxLines != null && maxLines! > 1 ? 15 : 16,
        ),
        counterText: maxLength == null ? null : '',
      ),
    );

    final disabled = !enabled;

    if (label == null) {
      return Opacity(opacity: disabled ? 0.45 : 1, child: field);
    }

    return Opacity(
      opacity: disabled ? 0.45 : 1,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [AppFieldLabel(label!), field],
      ),
    );
  }
}

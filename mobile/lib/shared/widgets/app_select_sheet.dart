import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import 'app_section_label.dart';

/// Tanlash varag'idagi bitta qator — `.brow`.
class AppSelectOption<T> {
  const AppSelectOption({required this.value, required this.label});

  final T value;
  final String label;
}

/// Pastdan chiqadigan tanlash varag'i — `tokens.css` `.bsheet` + `.brow`.
///
/// Dizaynda pill dropdown (`.fdrop`) bosilganda shu varaq ochiladi:
/// tutqich (40×4) · sarlavha (18/750) · qatorlar (15px, orasida hairline) ·
/// tanlangan qator `--action` rangda va yonida ✓.
///
/// Tanlangan qiymatni qaytaradi; bekor qilinsa `null`.
Future<T?> showAppSelectSheet<T>({
  required BuildContext context,
  required String title,
  required List<AppSelectOption<T>> options,
  T? selected,
}) {
  return showModalBottomSheet<T>(
    context: context,
    backgroundColor: AppColors.surface,
    barrierColor: AppColors.scrim,
    isScrollControlled: true,
    shape: const RoundedRectangleBorder(borderRadius: AppRadius.sheetRadius),
    builder: (ctx) => AppSelectSheetBody<T>(
      title: title,
      options: options,
      selected: selected,
    ),
  );
}

/// `.bsheet` ichki qismi — alohida ham ishlatish mumkin.
class AppSelectSheetBody<T> extends StatelessWidget {
  const AppSelectSheetBody({
    super.key,
    required this.title,
    required this.options,
    this.selected,
  });

  final String title;
  final List<AppSelectOption<T>> options;
  final T? selected;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 14, 24, AppSpacing.s6),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const AppSheetHandle(),
            Text(
              title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: AppColors.ink,
              ),
            ),
            const SizedBox(height: AppSpacing.s2),
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: options.length,
                itemBuilder: (ctx, i) {
                  final option = options[i];
                  final isSelected = option.value == selected;
                  final isLast = i == options.length - 1;
                  return Material(
                    type: MaterialType.transparency,
                    child: InkWell(
                      onTap: () => Navigator.of(ctx).pop(option.value),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 2,
                          vertical: 14,
                        ),
                        decoration: BoxDecoration(
                          border: isLast
                              ? null
                              : const Border(
                                  bottom: BorderSide(color: AppColors.line),
                                ),
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(
                                option.label,
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: isSelected
                                      ? FontWeight.w700
                                      : FontWeight.w500,
                                  color: isSelected
                                      ? AppColors.action
                                      : AppColors.ink,
                                ),
                              ),
                            ),
                            if (isSelected)
                              const Icon(
                                Icons.check,
                                size: 18,
                                color: AppColors.action,
                              ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Formadagi tanlash maydoni — `redesign4/phones/add-phone.html`.
///
/// Ko'rinishi input bilan bir xil (`.inp` 52px + `expand_more` dumi), bosilganda
/// [showAppSelectSheet] ochiladi. `Form` bilan ishlashi uchun `FormField`
/// ustiga qurilgan — mavjud validatorlar aynan shu holicha uzatiladi.
class AppSelectField<T> extends StatelessWidget {
  const AppSelectField({
    super.key,
    this.label,
    required this.sheetTitle,
    required this.value,
    required this.options,
    required this.onChanged,
    this.validator,
    this.hint = '—',
    this.enabled = true,
  });

  final String? label;
  final String sheetTitle;
  final T? value;
  final List<AppSelectOption<T>> options;
  final ValueChanged<T?> onChanged;
  final String? Function(T?)? validator;
  final String hint;
  final bool enabled;

  String? _labelFor(T? v) {
    for (final o in options) {
      if (o.value == v) return o.label;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return FormField<T>(
      initialValue: value,
      validator: validator,
      builder: (state) {
        final current = state.value;
        final text = _labelFor(current);
        final hasError = state.hasError;

        return Opacity(
          opacity: enabled ? 1 : 0.45,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (label != null) AppFieldLabel(label!),
              Material(
                type: MaterialType.transparency,
                child: InkWell(
                  onTap: enabled
                      ? () async {
                          final picked = await showAppSelectSheet<T>(
                            context: context,
                            title: sheetTitle,
                            options: options,
                            selected: current,
                          );
                          if (picked == null && current == null) return;
                          state.didChange(picked);
                          onChanged(picked);
                        }
                      : null,
                  borderRadius: AppRadius.inputRadius,
                  child: Container(
                    height: 52,
                    padding: const EdgeInsets.symmetric(horizontal: 15),
                    decoration: BoxDecoration(
                      color: AppColors.card,
                      borderRadius: AppRadius.inputRadius,
                      border: Border.all(
                        color: hasError ? AppColors.neg : Colors.transparent,
                        width: 1.5,
                      ),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            text ?? hint,
                            style: AppText.input.copyWith(
                              color: text == null
                                  ? AppColors.ink3
                                  : AppColors.ink,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const Icon(
                          Icons.expand_more,
                          size: 18,
                          color: AppColors.ink3,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              if (hasError)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    state.errorText!,
                    style: const TextStyle(fontSize: 12, color: AppColors.neg),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}

/// `.bsheet .handle` — 40×4, `--line-strong`, pastida 14px bo'shliq.
class AppSheetHandle extends StatelessWidget {
  const AppSheetHandle({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        width: 40,
        height: 4,
        margin: const EdgeInsets.only(bottom: 14),
        decoration: BoxDecoration(
          color: AppColors.lineStrong,
          borderRadius: BorderRadius.circular(2),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import 'app_danger_button.dart';
import 'app_primary_button.dart';
import 'app_secondary_button.dart';

/// Markaziy dialog — `r4.css` `.dialog`.
///
/// `--surface` fon · 16px radius · sarlavha 18/750 · matn 14/`--ink-2` ·
/// harakatlar o'ngda (ghost + solid/danger).
///
/// Tasdiqlansa `true`, bekor qilinsa `false`/`null` qaytadi — chaqiruvchi
/// mantiq o'zgarmasligi uchun natija shakli oddiy `bool?`.
Future<bool?> showAppConfirmDialog({
  required BuildContext context,
  required String title,
  Widget? content,
  String cancelLabel = 'Bekor qilish',
  required String confirmLabel,
  bool isDanger = false,
}) {
  return showDialog<bool>(
    context: context,
    barrierColor: AppColors.scrim,
    builder: (ctx) => AlertDialog(
      insetPadding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s6,
        vertical: AppSpacing.s6,
      ),
      contentPadding: const EdgeInsets.fromLTRB(22, 10, 22, 0),
      titlePadding: const EdgeInsets.fromLTRB(22, 22, 22, 0),
      actionsPadding: const EdgeInsets.fromLTRB(22, 18, 22, 14),
      title: Text(title),
      content: content,
      actions: [
        AppSecondaryButton(
          label: cancelLabel,
          onPressed: () => Navigator.pop(ctx, false),
        ),
        const SizedBox(width: 6),
        if (isDanger)
          AppDangerButton(
            label: confirmLabel,
            onPressed: () => Navigator.pop(ctx, true),
          )
        else
          AppPrimaryButton(
            label: confirmLabel,
            onPressed: () => Navigator.pop(ctx, true),
          ),
      ],
    ),
  );
}

/// `.dg-b` uslubidagi dialog matni — `<b>` bo'laklari `--ink` rangda.
class AppDialogText extends StatelessWidget {
  const AppDialogText({super.key, required this.text, this.emphasis});

  /// Oddiy matn. [emphasis] berilsa, u matnning boshida qalin ko'rsatiladi.
  final String text;
  final String? emphasis;

  @override
  Widget build(BuildContext context) {
    const base = TextStyle(
      fontSize: 14,
      height: 1.5,
      color: AppColors.ink2,
    );
    if (emphasis == null) return Text(text, style: base);

    return Text.rich(
      TextSpan(
        style: base,
        children: [
          TextSpan(
            text: emphasis,
            style: const TextStyle(
              color: AppColors.ink,
              fontWeight: FontWeight.w700,
            ),
          ),
          TextSpan(text: text),
        ],
      ),
    );
  }
}

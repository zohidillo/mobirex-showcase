import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Ikkilamchi (ghost) tugma — `tokens.css` `.btn-ghost`
/// va `r4.css` `.btn-ghost.danger`.
///
/// 44px balandlik · fon YO'Q · `--ink-3` matn (danger: `--neg`) · 10px radius.
/// Bosilganda `--card-pressed` fon paydo bo'ladi va matn `--ink` ga o'tadi.
class AppSecondaryButton extends StatefulWidget {
  const AppSecondaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
    this.isDanger = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;

  /// `.btn-ghost.danger` — matn `--neg` rangda.
  final bool isDanger;

  @override
  State<AppSecondaryButton> createState() => _AppSecondaryButtonState();
}

class _AppSecondaryButtonState extends State<AppSecondaryButton> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onPressed != null;
    final pressed = _pressed && enabled;

    final Color fg = widget.isDanger
        ? AppColors.neg
        : (pressed ? AppColors.ink : AppColors.ink3);

    return Opacity(
      opacity: enabled ? 1 : 0.45,
      child: AnimatedContainer(
        duration: AppDurations.press,
        curve: AppCurves.press,
        height: 44,
        decoration: BoxDecoration(
          color: pressed ? AppColors.cardPressed : Colors.transparent,
          borderRadius: AppRadius.inputRadius,
        ),
        child: Material(
          type: MaterialType.transparency,
          child: InkWell(
            onTap: widget.onPressed,
            onHighlightChanged: (v) {
              if (_pressed != v) setState(() => _pressed = v);
            },
            borderRadius: AppRadius.inputRadius,
            splashColor: Colors.transparent,
            highlightColor: Colors.transparent,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (widget.icon != null) ...[
                    Icon(widget.icon, size: 18, color: fg),
                    const SizedBox(width: 6),
                  ],
                  Text(
                    widget.label,
                    style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w600,
                      color: fg,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

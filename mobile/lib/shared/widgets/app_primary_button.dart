import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Asosiy (solid) tugma — `tokens.css` `.btn-solid` / `.btn-block`.
///
/// 44px balandlik (block: 54px) — Apple 44pt minimal tegish maydoni · `--action` fon · `--on-action` matn ·
/// 10px radius. Bosilganda `--action-pressed` + 1px pastga siljish, 120ms.
/// O'chirilgan: opacity .45. Yuklanmoqda: opacity .7 + kichik spinner.
class AppPrimaryButton extends StatefulWidget {
  const AppPrimaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
    this.isLoading = false,
    this.block = false,
  });

  final String label;

  /// `null` — o'chirilgan holat.
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isLoading;

  /// To'liq kenglik, 54px balandlik, 15px matn.
  final bool block;

  @override
  State<AppPrimaryButton> createState() => _AppPrimaryButtonState();
}

class _AppPrimaryButtonState extends State<AppPrimaryButton> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onPressed != null && !widget.isLoading;
    final double opacity = widget.onPressed == null
        ? 0.45
        : (widget.isLoading ? 0.7 : 1.0);

    return Opacity(
      opacity: opacity,
      child: AnimatedContainer(
        duration: AppDurations.press,
        curve: AppCurves.press,
        width: widget.block ? double.infinity : null,
        height: widget.block ? 54 : 44,
        transform: Matrix4.translationValues(0, _pressed && enabled ? 1 : 0, 0),
        decoration: BoxDecoration(
          color: _pressed && enabled
              ? AppColors.actionPressed
              : AppColors.action,
          borderRadius: AppRadius.inputRadius,
        ),
        child: Material(
          type: MaterialType.transparency,
          child: InkWell(
            onTap: enabled ? widget.onPressed : null,
            onHighlightChanged: (v) {
              if (_pressed != v) setState(() => _pressed = v);
            },
            borderRadius: AppRadius.inputRadius,
            splashColor: Colors.transparent,
            highlightColor: Colors.transparent,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.s5),
              child: Center(
                child: widget.isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 3,
                          color: AppColors.onAction,
                          backgroundColor: AppColors.overlayPressed,
                        ),
                      )
                    : Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (widget.icon != null) ...[
                            Icon(
                              widget.icon,
                              size: 18,
                              color: AppColors.onAction,
                            ),
                            const SizedBox(width: 6),
                          ],
                          Text(
                            widget.label,
                            style: TextStyle(
                              fontSize: widget.block ? 15 : 13,
                              fontWeight: FontWeight.w800,
                              color: AppColors.onAction,
                            ),
                          ),
                        ],
                      ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

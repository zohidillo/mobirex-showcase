import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Xavfli harakat tugmasi — `r4.css` `.btn-danger`.
///
/// 44px balandlik (block: 54px) — Apple 44pt minimal tegish maydoni · `--neg` fon · `--on-action` matn ·
/// 10px radius. Bosilganda opacity .85 + 1px pastga siljish.
class AppDangerButton extends StatefulWidget {
  const AppDangerButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
    this.isLoading = false,
    this.block = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isLoading;
  final bool block;

  @override
  State<AppDangerButton> createState() => _AppDangerButtonState();
}

class _AppDangerButtonState extends State<AppDangerButton> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onPressed != null && !widget.isLoading;
    final pressed = _pressed && enabled;
    final double opacity = widget.onPressed == null
        ? 0.45
        : (pressed ? 0.85 : (widget.isLoading ? 0.7 : 1.0));

    return Opacity(
      opacity: opacity,
      child: AnimatedContainer(
        duration: AppDurations.press,
        curve: AppCurves.press,
        width: widget.block ? double.infinity : null,
        height: widget.block ? 54 : 44,
        transform: Matrix4.translationValues(0, pressed ? 1 : 0, 0),
        decoration: const BoxDecoration(
          color: AppColors.neg,
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
              padding: const EdgeInsets.symmetric(horizontal: 18),
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

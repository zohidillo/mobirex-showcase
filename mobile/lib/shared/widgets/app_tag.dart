import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Yorliq o'lchami — `r4.css` `.dirtag` (26px) va `.sttag` (24px).
enum AppTagSize { direction, status }

/// Chegarali holat yorlig'i — `.dirtag` / `.sttag`.
///
/// Foni YO'Q: 1px chegara + shu rangdagi matn (UPPERCASE, 800, ls +0.08em).
/// Qarzlarda yo'nalish (`--pos` / `--neg`), murojaatlarda holat
/// (`--warn` ochiq, `--pos` yopilgan) uchun ishlatiladi.
class AppTag extends StatelessWidget {
  const AppTag({
    super.key,
    required this.label,
    required this.color,
    this.size = AppTagSize.direction,
  });

  final String label;
  final Color color;
  final AppTagSize size;

  @override
  Widget build(BuildContext context) {
    final isDirection = size == AppTagSize.direction;
    return Container(
      height: isDirection ? 26 : 24,
      padding: EdgeInsets.symmetric(horizontal: isDirection ? 10 : 9),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        borderRadius: AppRadius.chipRadius,
        border: Border.all(color: color),
      ),
      child: Text(
        label.toUpperCase(),
        style: TextStyle(
          fontSize: isDirection ? 10.5 : 10,
          fontWeight: FontWeight.w800,
          letterSpacing: isDirection ? 0.84 : 0.8,
          color: color,
        ),
      ),
    );
  }
}

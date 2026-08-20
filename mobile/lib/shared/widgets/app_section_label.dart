import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Bo'lim sarlavhasi — `tokens.css` `.sect-h`.
///
/// 11px · 800 · UPPERCASE · ls +0.14em · `--ink-3`, tepasida 24px,
/// pastida 10px bo'shliq.
class AppSectionLabel extends StatelessWidget {
  const AppSectionLabel(
    this.text, {
    super.key,
    this.padding = const EdgeInsets.only(top: AppSpacing.s6, bottom: 10),
  });

  final String text;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: padding,
      child: Text(text.toUpperCase(), style: AppText.sectionLabel),
    );
  }
}

/// Input ustidagi yorliq — `tokens.css` `.f label`.
///
/// 10.5px · 700 · UPPERCASE · ls +0.12em · `--ink-3`.
class AppFieldLabel extends StatelessWidget {
  const AppFieldLabel(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 7),
      child: Text(
        text.toUpperCase(),
        style: AppText.meta.copyWith(
          fontWeight: FontWeight.w700,
          letterSpacing: 1.26,
        ),
      ),
    );
  }
}

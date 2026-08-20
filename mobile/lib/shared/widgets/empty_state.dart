import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

/// Bo'sh holat — `redesign3/unsold-phones.html` `.stateview`.
///
/// 44px ikon (`--ink-3`) · 15px xabar (`--ink-2`, lh 1.5) · matnli
/// "Yangilash" havolasi (`.slink`).
class EmptyState extends StatelessWidget {
  final String message;
  final IconData icon;
  final VoidCallback? onRefresh;

  const EmptyState({
    super.key,
    required this.message,
    this.icon = Icons.inbox_outlined,
    this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.s8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 44, color: AppColors.ink3),
            const SizedBox(height: 14),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppColors.ink2,
                fontSize: 15,
                height: 1.5,
              ),
            ),
            if (onRefresh != null) ...[
              const SizedBox(height: 14),
              StateLink(
                label: 'Yangilash',
                icon: Icons.refresh,
                onTap: onRefresh!,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// `.slink` — 13.5px · 700 · `--action`, ikon bilan matnli havola.
class StateLink extends StatelessWidget {
  const StateLink({
    super.key,
    required this.label,
    required this.icon,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      type: MaterialType.transparency,
      child: InkWell(
        onTap: onTap,
        borderRadius: AppRadius.inputRadius,
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.s3,
            vertical: AppSpacing.s2,
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, size: 18, color: AppColors.action),
              const SizedBox(width: 7),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 13.5,
                  fontWeight: FontWeight.w700,
                  color: AppColors.action,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

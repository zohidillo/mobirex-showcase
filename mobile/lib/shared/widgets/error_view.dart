import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import 'app_primary_button.dart';

/// Xatolik holati — `redesign3/unsold-phones.html` `.stateview` (`.sicon.err`).
///
/// 44px `--neg` ikon · 15px xabar (`--ink-2`, lh 1.5) · "Qayta urinish"
/// solid tugmasi. Callback imzosi o'zgarmadi (`onRetry`).
class ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const ErrorView({super.key, required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.s8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 44, color: AppColors.neg),
            const SizedBox(height: 14),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 15,
                height: 1.5,
                color: AppColors.ink2,
              ),
            ),
            if (onRetry != null) ...[
              const SizedBox(height: 14),
              AppPrimaryButton(
                label: 'Qayta urinish',
                icon: Icons.refresh,
                onPressed: onRetry,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class OfflineView extends StatelessWidget {
  final VoidCallback? onRetry;

  const OfflineView({super.key, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return ErrorView(
      message:
          "Internet aloqasi yo'q.\nUlanishni tekshirib, qayta urinib ko'ring.",
      onRetry: onRetry,
    );
  }
}

/// Ichki (inline) xato bloki — `redesign3/login.html` `.ierr`.
///
/// Fon YO'Q: 1px `--neg` chegara, 10px radius, 13px `--neg` matn.
class InlineError extends StatelessWidget {
  final String message;

  const InlineError({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: 14,
        vertical: AppSpacing.s3,
      ),
      decoration: BoxDecoration(
        borderRadius: AppRadius.inputRadius,
        border: Border.all(color: AppColors.neg),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, color: AppColors.neg, size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: AppColors.neg,
                fontSize: 13,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

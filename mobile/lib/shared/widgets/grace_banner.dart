import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/constants/app_links.dart';
import '../../core/theme/app_theme.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';

/// In-memory dismiss flag for the grace banner. It intentionally lives in
/// memory only: the banner reappears the next time the app is opened, which is
/// the desired nudge cadence for an unpaid account.
final graceBannerDismissedProvider = StateProvider<bool>((ref) => false);

/// Whether the grace banner should currently be shown. Combines the billing
/// state (grace && not VIP), a non-empty warning message (guard), and the
/// session dismiss flag. AppShell watches this both to render the banner and
/// to compensate the page's top inset.
final graceBannerVisibleProvider = Provider<bool>((ref) {
  final inGrace = ref.watch(showGraceBannerProvider);
  final dismissed = ref.watch(graceBannerDismissedProvider);
  final message = ref.watch(billingStatusProvider)?.warningMessage ?? '';
  return inGrace && !dismissed && message.trim().isNotEmpty;
});

/// Grace banner — `redesign3/unsold-phones.html` `.grace` (9-ramka).
///
/// `--warn` fon, `--on-action` matn. Bloklamaydigan ogohlantirish:
/// xabar (13/700) + qolgan kunlar (13/800) + "Hisobni to'ldirish" havolasi.
///
/// ⚠️ Billing mantig'i va providerlar tegilmadi — faqat ko'rinish.
class GraceBanner extends ConsumerWidget {
  const GraceBanner({super.key});

  Future<void> _topUp(BuildContext context) async {
    final uri = Uri.parse(AppLinks.telegramSupportUrl);
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Telegram: ${AppLinks.telegramSupportUrl}'),
            backgroundColor: AppColors.neg,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final billing = ref.watch(billingStatusProvider);
    if (billing == null) return const SizedBox.shrink();

    // `--on-action` — amber ustidagi to'q matn.
    const onWarning = AppColors.onAction;

    final daysLeft = billing.graceDaysLeft;

    return Material(
      color: AppColors.warn,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          AppSpacing.s3,
          10,
          AppSpacing.s3,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(
              Icons.warning_amber_rounded,
              color: onWarning,
              size: 22,
            ),
            const SizedBox(width: AppSpacing.s3),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    billing.warningMessage,
                    style: const TextStyle(
                      color: onWarning,
                      fontSize: 13,
                      height: 1.35,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  if (daysLeft != null) ...[
                    const SizedBox(height: 3),
                    Text(
                      '$daysLeft kun qoldi',
                      style: const TextStyle(
                        color: onWarning,
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ],
                  const SizedBox(height: AppSpacing.s2),
                  // `.gl` — tagi chizilgan havola.
                  Material(
                    type: MaterialType.transparency,
                    child: InkWell(
                      onTap: () => _topUp(context),
                      borderRadius: AppRadius.chipRadius,
                      child: const Padding(
                        padding: EdgeInsets.symmetric(vertical: 2),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.account_balance_wallet_outlined,
                              size: 18,
                              color: onWarning,
                            ),
                            SizedBox(width: 6),
                            Text(
                              "Hisobni to'ldirish",
                              style: TextStyle(
                                color: onWarning,
                                fontSize: 12.5,
                                fontWeight: FontWeight.w800,
                                decoration: TextDecoration.underline,
                                decorationColor: onWarning,
                                decorationThickness: 1.2,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            // `.gx` — yopish.
            Material(
              type: MaterialType.transparency,
              child: InkWell(
                onTap: () =>
                    ref.read(graceBannerDismissedProvider.notifier).state = true,
                borderRadius: AppRadius.chipRadius,
                child: const Tooltip(
                  message: 'Yopish',
                  child: Padding(
                    padding: EdgeInsets.all(AppSpacing.s1),
                    child: Icon(Icons.close, color: onWarning, size: 18),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/constants/app_links.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../providers/auth_provider.dart';

/// Full-screen state shown when the account is billing-blocked. Calm, blame-free
/// tone. The user stays signed in — there is NO automatic logout; the only way
/// out is topping up (contact) or the manual, secondary "Chiqish" button.
class BlockedPage extends ConsumerWidget {
  const BlockedPage({super.key});

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
    final user = ref.watch(authProvider).user;
    final billing = user?.billing;
    final message = billing?.blockedMessage ?? '';

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Center(
                    child: Icon(
                      Icons.pause_circle_outline,
                      color: AppColors.warn,
                      size: 44,
                    ),
                  ),
                  const SizedBox(height: 14),
                  const Text(
                    'Hisobingiz vaqtincha to‘xtatilgan',
                    textAlign: TextAlign.center,
                    style: AppText.title,
                  ),
                  if (message.trim().isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: AppSpacing.s3),
                      child: Text(
                        message,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: AppColors.ink2,
                          fontSize: 15,
                          height: 1.5,
                        ),
                      ),
                    ),
                  const SizedBox(height: AppSpacing.s6),
                  _BalanceCard(balance: user?.balance),
                  const SizedBox(height: AppSpacing.s7),
                  AppPrimaryButton(
                    label: "Hisobni to‘ldirish",
                    icon: Icons.account_balance_wallet_outlined,
                    block: true,
                    onPressed: () => _topUp(context),
                  ),
                  const SizedBox(height: AppSpacing.s2),
                  TextButton(
                    onPressed: () => ref.read(authProvider.notifier).logout(),
                    style: TextButton.styleFrom(
                      foregroundColor: AppColors.neg,
                      minimumSize: const Size(double.infinity, 44),
                    ),
                    child: const Text(
                      'Chiqish',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
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

class _BalanceCard extends StatelessWidget {
  final String? balance;

  const _BalanceCard({this.balance});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s4,
        vertical: 13,
      ),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppRadius.cardRadius,
        boxShadow: AppShadows.card,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text('Joriy balans'.toUpperCase(), style: AppText.sectionLabel),
          Text(
            formatMoney(balance),
            style: AppText.totalValue.copyWith(color: AppColors.neg),
          ),
        ],
      ),
    );
  }
}

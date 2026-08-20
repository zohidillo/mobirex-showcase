import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/constants/app_links.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_section_label.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../providers/support_provider.dart';
import '../widgets/support_request_card.dart';
import '../widgets/support_request_form.dart';

class SupportPage extends ConsumerWidget {
  const SupportPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final listState = ref.watch(supportListProvider);

    return Scaffold(
      appBar: VelmoraAppBar(subtitle: 'Yordam va murojaat', showDrawer: true),
      body: RefreshIndicator(
        color: AppColors.action,
        backgroundColor: AppColors.card,
        onRefresh: () =>
            ref.read(supportListProvider.notifier).load(refresh: true),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.s4,
            14,
            AppSpacing.s4,
            AppSpacing.s8,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _TelegramCard(),
              const AppSectionLabel('Murojaat yuborish'),
              const AppCard(child: SupportRequestForm()),
              const AppSectionLabel('Murojaatlarim'),
              if (listState.isLoading)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: AppSpacing.s8),
                  child: Center(
                    child: SizedBox(
                      width: 42,
                      height: 42,
                      child: CircularProgressIndicator(strokeWidth: 3.5),
                    ),
                  ),
                )
              else if (listState.error != null)
                ErrorView(
                  message: 'Xatolik yuz berdi',
                  onRetry: () => ref
                      .read(supportListProvider.notifier)
                      .load(refresh: true),
                )
              else if (listState.items.isEmpty)
                const EmptyState(
                  message: "Ma'lumot topilmadi",
                  icon: Icons.inbox_outlined,
                )
              else
                Column(
                  children: [
                    for (final r in listState.items)
                      Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.s3),
                        child: SupportRequestCard(
                          request: r,
                          onTap: () => context.push('/support/detail/${r.id}'),
                        ),
                      ),
                    if (listState.hasMore)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: listState.isLoadingMore
                            ? const Center(
                                child: Padding(
                                  padding: EdgeInsets.all(14),
                                  child: SizedBox(
                                    width: 28,
                                    height: 28,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 3,
                                    ),
                                  ),
                                ),
                              )
                            : TextButton(
                                onPressed: () => ref
                                    .read(supportListProvider.notifier)
                                    .loadMore(),
                                child: const Text("Ko'proq yuklash"),
                              ),
                      ),
                  ],
                ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}

class _TelegramCard extends StatelessWidget {
  const _TelegramCard();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: () async {
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
        },
        borderRadius: AppRadius.cardRadius,
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.s4),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppColors.action,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.send,
                  color: AppColors.onAction,
                  size: 22,
                ),
              ),
              const SizedBox(width: 16),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Telegram support', style: AppText.bodyLg),
                    SizedBox(height: 2),
                    Text(
                      'Telegram orqali tezkor yordam oling',
                      style: TextStyle(color: AppColors.ink2, fontSize: 13),
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.chevron_right,
                size: 20,
                color: AppColors.ink3,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

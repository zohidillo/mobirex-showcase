import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/router/navigation_helper.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_section_label.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../widgets/account_delete_form.dart';

class AccountDeleteRequestPage extends ConsumerWidget {
  const AccountDeleteRequestPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    if (user == null) return const SizedBox.shrink();

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: "Accountni o'chirish so'rovi",
        onBack: () => goBack(context, ref, fallbackRoute: '/profile'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          AppSpacing.s8,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppCard(
              edge: AppCardEdge.negative,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.info_outline,
                    color: AppColors.warn,
                    size: 18,
                  ),
                  const SizedBox(width: AppSpacing.s3),
                  const Expanded(
                    child: Text(
                      "Bu so'rov accountingizni darhol o'chirmaydi. "
                      "Sizning so'rovingiz ko'rib chiqiladi va tez orada "
                      "siz bilan bog'lanamiz.",
                      style: TextStyle(
                        fontSize: 13,
                        height: 1.45,
                        color: AppColors.ink2,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const AppSectionLabel("Ma'lumotlar"),
            AppCard(
              child: AccountDeleteForm(
                user: user,
                onSuccess: () =>
                    goBack(context, ref, fallbackRoute: '/profile'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_dialog.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_secondary_button.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_tag.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../data/models/debt_model.dart';
import '../providers/debt_provider.dart';
import 'pay_debt_dialog.dart';

/// To'lov tarixi varag'i — `redesign4/debts/unpaid-debts.html` (13-14 frame).
///
/// Providerlar va mantiq o'zgarmadi — faqat ko'rinish.
class DebtPaymentHistorySheet extends ConsumerWidget {
  final DebtModel debt;
  final bool isOwner;
  final bool canPay;
  final bool canDelete;
  final Future<String?> Function(String amount, {String? note}) onPay;
  final VoidCallback? onDeleteDebt;

  const DebtPaymentHistorySheet({
    super.key,
    required this.debt,
    required this.isOwner,
    required this.canPay,
    required this.canDelete,
    required this.onPay,
    this.onDeleteDebt,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final paymentsState = ref.watch(debtPaymentsProvider(debt.id));
    final directionColor = debt.isWeGave ? AppColors.pos : AppColors.neg;

    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      expand: false,
      builder: (context, scrollCtrl) {
        return Column(
          children: [
            // drag handle
            const AppSheetHandle(),
            // header
            _DebtSummaryHeader(
              debt: debt,
              directionColor: directionColor,
              canPay: canPay,
              canDelete: canDelete,
              onPay: () => _showPayDialog(context, ref),
              onDelete: onDeleteDebt,
            ),
            Container(height: 1, color: AppColors.line),
            // payment history list
            Expanded(
              child: _PaymentHistoryBody(
                state: paymentsState,
                isOwner: isOwner,
                onRetry: () =>
                    ref.read(debtPaymentsProvider(debt.id).notifier).load(),
                onDeletePayment: (paymentId) =>
                    _confirmDeletePayment(context, ref, paymentId),
                scrollCtrl: scrollCtrl,
              ),
            ),
          ],
        );
      },
    );
  }

  void _showPayDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (_) => PayDebtDialog(
        debt: debt,
        onPay: (String amount, {String? note}) async {
          final err = await onPay(amount, note: note);
          if (err == null) {
            ref.read(debtPaymentsProvider(debt.id).notifier).load();
          }
          return err;
        },
      ),
    );
  }

  Future<void> _confirmDeletePayment(
    BuildContext context,
    WidgetRef ref,
    int paymentId,
  ) async {
    final ok = await showAppConfirmDialog(
      context: context,
      title: 'To\'lovni o\'chirish',
      content: const AppDialogText(
        text: 'Bu to\'lov o\'chirilsinmi? Kapital qaytariladi.',
      ),
      confirmLabel: 'O\'chirish',
      isDanger: true,
    );
    if (ok == true && context.mounted) {
      final err = await ref
          .read(debtPaymentsProvider(debt.id).notifier)
          .deletePayment(paymentId);
      if (err != null && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(parseApiError(err)),
            backgroundColor: AppColors.neg,
          ),
        );
      }
    }
  }
}

// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------

class _DebtSummaryHeader extends StatelessWidget {
  final DebtModel debt;
  final Color directionColor;
  final bool canPay;
  final bool canDelete;
  final VoidCallback onPay;
  final VoidCallback? onDelete;

  const _DebtSummaryHeader({
    required this.debt,
    required this.directionColor,
    required this.canPay,
    required this.canDelete,
    required this.onPay,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 4, 24, AppSpacing.s4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  debt.fName,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: AppColors.ink,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 10),
              AppTag(
                label: debt.directionDisplay.isNotEmpty
                    ? debt.directionDisplay
                    : debt.direction,
                color: directionColor,
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text.rich(
            TextSpan(
              text: formatMoney(debt.remainingAmount),
              style: AppText.display.copyWith(color: directionColor),
              children: [
                TextSpan(
                  text: ' jami ${formatMoney(debt.amount)}',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0,
                    color: AppColors.ink3,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 7),
            child: Text(
              [
                formatDateShort(debt.addedAt),
                if (debt.createdBy != null) debt.createdBy!.username,
                if (debt.branch != null) debt.branch!.name,
              ].join(' · '),
              style: AppText.meta,
            ),
          ),
          if (debt.note != null && debt.note!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 5),
              child: Text(
                debt.note!,
                style: const TextStyle(color: AppColors.ink2, fontSize: 12.5),
              ),
            ),
          if (canPay || (canDelete && onDelete != null))
            Padding(
              padding: const EdgeInsets.only(top: AppSpacing.s3),
              child: Row(
                children: [
                  const Spacer(),
                  if (canDelete && onDelete != null) ...[
                    AppSecondaryButton(
                      label: 'O\'chirish',
                      onPressed: onDelete,
                      isDanger: true,
                    ),
                    const SizedBox(width: 6),
                  ],
                  if (canPay)
                    AppPrimaryButton(label: 'To\'lash', onPressed: onPay),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------

class _PaymentHistoryBody extends StatelessWidget {
  final DebtPaymentsState state;
  final bool isOwner;
  final VoidCallback onRetry;
  final Future<void> Function(int paymentId) onDeletePayment;
  final ScrollController scrollCtrl;

  const _PaymentHistoryBody({
    required this.state,
    required this.isOwner,
    required this.onRetry,
    required this.onDeletePayment,
    required this.scrollCtrl,
  });

  @override
  Widget build(BuildContext context) {
    if (state.isLoading) {
      return const Center(
        child: SizedBox(
          width: 42,
          height: 42,
          child: CircularProgressIndicator(strokeWidth: 3.5),
        ),
      );
    }

    if (state.error != null) {
      return ErrorView(message: parseApiError(state.error), onRetry: onRetry);
    }

    if (state.payments.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(AppSpacing.s8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.payment_outlined,
                size: 44,
                color: AppColors.ink3,
              ),
              SizedBox(height: 14),
              Text(
                'To\'lovlar mavjud emas',
                style: TextStyle(
                  color: AppColors.ink2,
                  fontSize: 15,
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(24, AppSpacing.s3, 24, AppSpacing.s2),
          child: Row(
            children: [
              Text('To\'lov tarixi'.toUpperCase(), style: AppText.sectionLabel),
              const Spacer(),
              Text(
                '${state.payments.length} ta to\'lov',
                style: AppText.meta,
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.separated(
            controller: scrollCtrl,
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.s4,
              0,
              AppSpacing.s4,
              AppSpacing.s6,
            ),
            itemCount: state.payments.length,
            separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.s2),
            itemBuilder: (_, i) => _PaymentTile(
              payment: state.payments[i],
              isOwner: isOwner,
              onDelete: () => onDeletePayment(state.payments[i].id),
            ),
          ),
        ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------

class _PaymentTile extends StatelessWidget {
  final DebtPayment payment;
  final bool isOwner;
  final VoidCallback onDelete;

  const _PaymentTile({
    required this.payment,
    required this.isOwner,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.card,
        borderRadius: AppRadius.cardRadius,
        boxShadow: AppShadows.card,
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: AppSpacing.s3),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.payment, color: AppColors.pos, size: 18),
            const SizedBox(width: AppSpacing.s3),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        formatMoney(payment.amount),
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: AppColors.pos,
                        ),
                      ),
                      if (payment.paidBy != null) ...[
                        const SizedBox(width: 6),
                        Text(
                          '· ${payment.paidBy!.username}',
                          style: const TextStyle(
                            color: AppColors.ink3,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 2),
                  Row(
                    children: [
                      Text(
                        formatDate(payment.addedAt),
                        style: const TextStyle(
                          color: AppColors.ink3,
                          fontSize: 12,
                        ),
                      ),
                      if (payment.note != null && payment.note!.isNotEmpty) ...[
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            payment.note!,
                            style: const TextStyle(
                              color: AppColors.ink3,
                              fontSize: 12,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
            if (isOwner)
              IconButton(
                icon: const Icon(
                  Icons.delete_outline,
                  color: AppColors.neg,
                  size: 18,
                ),
                onPressed: onDelete,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                tooltip: 'To\'lovni o\'chirish',
              ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------

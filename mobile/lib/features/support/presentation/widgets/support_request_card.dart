import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_tag.dart';
import '../../data/models/support_request_model.dart';

/// Murojaat kartasi — `redesign4/support/support-list.html`.
///
/// Sarlavha — murojaat turi, o'ngda holat yorlig'i (`.sttag`);
/// ostida xabar qisqartmasi va meta qatori.
class SupportRequestCard extends StatelessWidget {
  final SupportRequest request;
  final VoidCallback onTap;

  const SupportRequestCard({
    super.key,
    required this.request,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final statusColor = _statusColor(request.status);
    final summary = request.message.length > 80
        ? '${request.message.substring(0, 80)}...'
        : request.message;

    final meta = <String>[
      formatDate(
        (request.lastMessageAt ?? request.createdAt).toIso8601String(),
      ),
      if (request.phone.isNotEmpty) request.phone,
    ].join(' · ');

    return AppCard(
      onTap: onTap,
      edge: request.unreadForUser
          ? AppCardEdge.positive
          : AppCardEdge.neutral,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  request.requestTypeDisplay.isNotEmpty
                      ? request.requestTypeDisplay
                      : _typeLabel(request.requestType),
                  style: AppText.bodyLg,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (request.unreadForUser) ...[
                const SizedBox(width: AppSpacing.s2),
                Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: AppColors.action,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                const Text(
                  "O'qilmagan",
                  style: TextStyle(
                    color: AppColors.action,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
              const SizedBox(width: AppSpacing.s2),
              AppTag(
                label: request.statusDisplay.isNotEmpty
                    ? request.statusDisplay
                    : _statusLabel(request.status),
                color: statusColor,
                size: AppTagSize.status,
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              summary,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: AppColors.ink2,
                fontSize: 13,
                height: 1.45,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 7),
            child: Text(
              meta,
              style: AppText.meta,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'IN_PROGRESS':
        return AppColors.warn;
      case 'RESOLVED':
        return AppColors.pos;
      case 'REJECTED':
        return AppColors.neg;
      default:
        return AppColors.ink2;
    }
  }

  String _statusLabel(String status) {
    switch (status) {
      case 'OPEN':
        return 'Yangi';
      case 'IN_PROGRESS':
        return 'Jarayonda';
      case 'RESOLVED':
        return 'Hal qilindi';
      case 'REJECTED':
        return 'Rad etildi';
      default:
        return status.isNotEmpty ? status : 'Yangi';
    }
  }

  String _typeLabel(String type) {
    switch (type) {
      case 'CONTACT':
        return 'Murojaat';
      case 'TECHNICAL':
        return 'Texnik masala';
      case 'ACCOUNT_DELETE':
        return "Accountni o'chirish";
      default:
        return type;
    }
  }
}

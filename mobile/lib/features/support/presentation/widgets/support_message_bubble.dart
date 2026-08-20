import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../data/models/support_message_model.dart';

/// Chat pufakchasi — `r4.css` `.msg.me` / `.msg.op`.
///
/// O'z xabaring — `--card-pressed`, o'ng pastki burchak 4px;
/// operator xabari — `--card`, chap pastki burchak 4px va tepasida
/// aksent rangdagi jo'natuvchi nomi.
class SupportMessageBubble extends StatelessWidget {
  final SupportMessage message;

  const SupportMessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.senderType == 'USER';
    final isSystem =
        message.senderType == 'SYSTEM' || message.senderType == 'EXTERNAL';

    if (isSystem) {
      return _SystemBubble(message: message);
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        mainAxisAlignment: isUser
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        children: [
          Flexible(
            child: Container(
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.78,
              ),
              padding: const EdgeInsets.symmetric(
                horizontal: 14,
                vertical: 11,
              ),
              decoration: BoxDecoration(
                color: isUser ? AppColors.cardPressed : AppColors.card,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(14),
                  topRight: const Radius.circular(14),
                  bottomLeft: Radius.circular(isUser ? 14 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 14),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (!isUser)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        _senderLabel(
                          message.senderType,
                          message.senderUsername,
                        ).toUpperCase(),
                        style: const TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.84,
                          color: AppColors.action,
                        ),
                      ),
                    ),
                  Text(
                    message.message,
                    style: const TextStyle(
                      color: AppColors.ink,
                      fontSize: 14,
                      height: 1.45,
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.only(top: 5),
                    child: Text(
                      formatDate(
                        message.createdAt.toIso8601String(),
                      ).toUpperCase(),
                      style: const TextStyle(
                        fontSize: 10,
                        letterSpacing: 0.6,
                        color: AppColors.ink3,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _senderLabel(String senderType, String? username) {
    switch (senderType) {
      case 'USER':
        return 'Siz';
      case 'ADMIN':
        return username != null ? 'Admin ($username)' : 'Admin';
      case 'SYSTEM':
        return 'Tizim';
      case 'EXTERNAL':
        return 'Tashqi';
      default:
        return senderType;
    }
  }
}

class _SystemBubble extends StatelessWidget {
  final SupportMessage message;

  const _SystemBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(
        vertical: AppSpacing.s2,
        horizontal: AppSpacing.s6,
      ),
      child: Column(
        children: [
          Text(
            message.message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.ink3,
              fontSize: 12,
              height: 1.45,
            ),
          ),
          const SizedBox(height: AppSpacing.s1),
          Text(
            formatDate(message.createdAt.toIso8601String()).toUpperCase(),
            style: const TextStyle(
              color: AppColors.ink3,
              fontSize: 10,
              letterSpacing: 0.6,
            ),
          ),
        ],
      ),
    );
  }
}

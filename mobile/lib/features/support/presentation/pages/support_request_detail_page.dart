import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/router/navigation_helper.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_tag.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../data/models/support_request_model.dart';
import '../providers/support_provider.dart';
import '../widgets/support_message_bubble.dart';

class SupportRequestDetailPage extends ConsumerStatefulWidget {
  final int requestId;

  const SupportRequestDetailPage({super.key, required this.requestId});

  @override
  ConsumerState<SupportRequestDetailPage> createState() =>
      _SupportRequestDetailPageState();
}

class _SupportRequestDetailPageState
    extends ConsumerState<SupportRequestDetailPage> {
  final _replyCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  @override
  void dispose() {
    _replyCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _replyCtrl.text.trim();
    if (text.isEmpty) return;

    _replyCtrl.clear();
    final error = await ref
        .read(supportDetailProvider(widget.requestId).notifier)
        .sendMessage(text);

    if (error != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error), backgroundColor: AppColors.neg),
      );
    } else {
      _scrollToBottom();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(supportDetailProvider(widget.requestId));

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Murojaat #${widget.requestId}',
        onBack: () => goBack(context, ref, fallbackRoute: '/support'),
      ),
      body: state.isLoading
          ? const Center(
              child: SizedBox(
                width: 42,
                height: 42,
                child: CircularProgressIndicator(strokeWidth: 3.5),
              ),
            )
          : state.error != null
          ? ErrorView(
              message: state.error!,
              onRetry: () => ref
                  .read(supportDetailProvider(widget.requestId).notifier)
                  .load(),
            )
          : Column(
              children: [
                if (state.request != null) _RequestInfoCard(state.request!),
                Expanded(
                  child: state.messages.isEmpty
                      ? const Center(
                          child: Text(
                            "Xabarlar yo'q",
                            style: TextStyle(
                              color: AppColors.ink2,
                              fontSize: 15,
                            ),
                          ),
                        )
                      : ListView.builder(
                          controller: _scrollCtrl,
                          padding: const EdgeInsets.fromLTRB(
                            AppSpacing.s4,
                            AppSpacing.s4,
                            AppSpacing.s4,
                            AppSpacing.s2,
                          ),
                          itemCount: state.messages.length,
                          itemBuilder: (ctx, i) =>
                              SupportMessageBubble(message: state.messages[i]),
                        ),
                ),
                _ReplyBar(
                  controller: _replyCtrl,
                  isSending: state.isSending,
                  onSend: _sendMessage,
                ),
              ],
            ),
    );
  }
}

/// Murojaat sarlavha kartasi — `redesign4/support/support-detail.html`.
class _RequestInfoCard extends StatelessWidget {
  final SupportRequest request;

  const _RequestInfoCard(this.request);

  @override
  Widget build(BuildContext context) {
    final statusColor = _statusColor(request.status);
    final meta = <String>[
      formatDate(request.createdAt.toIso8601String()),
      if (request.phone.isNotEmpty) request.phone,
    ].join(' · ');

    return Padding(
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.s4,
        AppSpacing.s3,
        AppSpacing.s4,
        0,
      ),
      child: AppCard(
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
                const SizedBox(width: 10),
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

class _ReplyBar extends StatelessWidget {
  final TextEditingController controller;
  final bool isSending;
  final VoidCallback onSend;

  const _ReplyBar({
    required this.controller,
    required this.isSending,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.s3,
          vertical: 10,
        ),
        decoration: const BoxDecoration(color: AppColors.surface),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                maxLines: 4,
                minLines: 1,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => onSend(),
                style: AppText.input,
                cursorColor: AppColors.action,
                decoration: const InputDecoration(
                  hintText: 'Javob yozish',
                  isDense: true,
                  contentPadding: EdgeInsets.symmetric(
                    horizontal: 15,
                    vertical: 13,
                  ),
                ),
              ),
            ),
            const SizedBox(width: AppSpacing.s2),
            // `.sendbtn` — 46px, aksent fon.
            SizedBox(
              width: 46,
              height: 46,
              child: Material(
                color: AppColors.action,
                borderRadius: AppRadius.cardRadius,
                child: InkWell(
                  onTap: isSending ? null : onSend,
                  borderRadius: AppRadius.cardRadius,
                  child: Center(
                    child: isSending
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 3,
                              color: AppColors.onAction,
                            ),
                          )
                        : const Icon(
                            Icons.send_rounded,
                            color: AppColors.onAction,
                            size: 20,
                          ),
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

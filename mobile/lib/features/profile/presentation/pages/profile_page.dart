import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../app.dart';
import '../../../../core/constants/app_links.dart';
import '../../../../core/theme/app_theme.dart';
// Tema almashtirish vaqtincha uzilgan (dizayn tizimi faqat qorong'i) —
// `_ThemeSection` bilan birga kommentda turibdi.
// import '../../../../core/theme/theme_provider.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_section_label.dart';
import '../../../../shared/widgets/app_tag.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../../shared/widgets/webview_page.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/profile_provider.dart';

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    if (user == null) return const SizedBox.shrink();

    return Scaffold(
      appBar: VelmoraAppBar(subtitle: 'Sozlamalar / Profil', showDrawer: true),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          AppSpacing.s8,
        ),
        children: [
          _ProfileCard(
            fullName: user.fullName,
            username: user.username,
            phone: user.phone,
          ),
          _SettingsSection(
            title: 'Hisob',
            children: [
              _SettingsTile(
                icon: Icons.person_outline,
                label: 'Foydalanuvchi nomini o\'zgartirish',
                onTap: () => user.isDemo
                    ? _showDemoBlocked(context)
                    : _showUsernameDialog(context, ref, user.username),
              ),
              _SettingsTile(
                icon: Icons.lock_outline,
                label: 'Parolni o\'zgartirish',
                onTap: () => user.isDemo
                    ? _showDemoBlocked(context)
                    : _showChangePasswordDialog(context, ref),
              ),
              _SettingsTile(
                icon: Icons.pin_outlined,
                label: user.hasPin ? 'PIN o\'zgartirish' : 'PIN o\'rnatish',
                onTap: () => user.isDemo
                    ? _showDemoBlocked(context)
                    : user.hasPin
                    ? context.go('/pin/change')
                    : context.go('/pin/setup'),
              ),
            ],
          ),
          // Tema tanlash vaqtincha yashirilgan — hozircha faqat qorong'i
          // tema mavjud. Ikkinchi palitra qo'shilganda qaytariladi:
          // _ThemeSection(),
          _BranchSection(user: user),
          _SettingsSection(
            title: "So'rovlar",
            children: [
              _SettingsTile(
                icon: Icons.delete_outline,
                label: "Hisobni o'chirish",
                onTap: () => user.isDemo
                    ? _showDemoBlockedUz(context)
                    : _showDeleteAccountFlow(context, ref),
              ),
            ],
          ),
          _SettingsSection(
            title: 'Yuridik',
            children: [
              _SettingsTile(
                icon: Icons.privacy_tip_outlined,
                label: 'Maxfiylik siyosati',
                onTap: () => _openWebView(
                  context,
                  AppLinks.privacyPolicyUrl,
                  'Maxfiylik siyosati',
                ),
              ),
              _SettingsTile(
                icon: Icons.description_outlined,
                label: 'Foydalanish shartlari',
                onTap: () =>
                    _openWebView(context, AppLinks.termsUrl, 'Shartlar'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Demo accounts cannot change credentials; the backend blocks it. We stop
  /// the action here so reviewers see a clear message instead of a raw error.
  void _showDemoBlocked(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('This action is disabled for demo accounts.'),
        backgroundColor: AppColors.neg,
      ),
    );
  }

  void _showDemoBlockedUz(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Demo hisob uchun bu amal mavjud emas.'),
        backgroundColor: AppColors.neg,
      ),
    );
  }

  void _openWebView(BuildContext context, String url, String title) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => WebViewPage(url: url, title: title),
      ),
    );
  }

  void _showUsernameDialog(
    BuildContext context,
    WidgetRef ref,
    String current,
  ) {
    final ctrl = TextEditingController(text: current);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Foydalanuvchi nomini o\'zgartirish'),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(
            labelText: 'Yangi foydalanuvchi nomi',
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Bekor qilish'),
          ),
          Consumer(
            builder: (context, ref, child) {
              final state = ref.watch(profileActionProvider);
              return ElevatedButton(
                onPressed: state is AsyncLoading
                    ? null
                    : () async {
                        final ok = await ref
                            .read(profileActionProvider.notifier)
                            .updateUsername(ctrl.text.trim());
                        if (ctx.mounted) {
                          if (ok) {
                            Navigator.pop(ctx);
                          } else {
                            final err = ref.read(profileActionProvider).error;
                            ScaffoldMessenger.of(ctx).showSnackBar(
                              SnackBar(
                                content: Text(parseApiError(err)),
                                backgroundColor: AppColors.neg,
                              ),
                            );
                          }
                        }
                      },
                child: const Text('Saqlash'),
              );
            },
          ),
        ],
      ),
    );
  }

  void _showChangePasswordDialog(BuildContext context, WidgetRef ref) {
    final oldCtrl = TextEditingController();
    final newCtrl = TextEditingController();
    final confirmCtrl = TextEditingController();
    String? error;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => AlertDialog(
          title: const Text('Parolni o\'zgartirish'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (error != null) ...[
                InlineError(message: error!),
                const SizedBox(height: 12),
              ],
              TextField(
                controller: oldCtrl,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Joriy parol'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: newCtrl,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Yangi parol'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: confirmCtrl,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Yangi parolni tasdiqlang',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Bekor qilish'),
            ),
            ElevatedButton(
              onPressed: () async {
                if (oldCtrl.text.isEmpty) {
                  setState(() => error = 'Joriy parol majburiy');
                  return;
                }
                if (newCtrl.text.isEmpty) {
                  setState(() => error = 'Yangi parol majburiy');
                  return;
                }
                if (confirmCtrl.text.isEmpty) {
                  setState(() => error = 'Yangi parolni tasdiqlash majburiy');
                  return;
                }
                if (newCtrl.text != confirmCtrl.text) {
                  setState(() => error = 'Parollar mos kelmadi');
                  return;
                }
                try {
                  await ref
                      .read(authProvider.notifier)
                      .changePassword(
                        oldPassword: oldCtrl.text,
                        newPassword: newCtrl.text,
                        newPasswordConfirm: confirmCtrl.text,
                      );
                  if (ctx.mounted) {
                    Navigator.pop(ctx);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Parol muvaffaqiyatli o\'zgartirildi'),
                        backgroundColor: AppColors.pos,
                      ),
                    );
                  }
                } catch (e) {
                  setState(() => error = parseApiError(e));
                }
              },
              child: const Text('Saqlash'),
            ),
          ],
        ),
      ),
    );
  }

  /// Two-step confirmation before permanently deleting the account. Real
  /// deletion only happens after both confirmations; on success the user is
  /// logged out (tokens cleared) and the router sends them to login.
  Future<void> _showDeleteAccountFlow(
    BuildContext context,
    WidgetRef ref,
  ) async {
    // Step 1: warning + intent.
    final firstConfirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Hisobni o'chirish"),
        content: const Text(
          "Hisobingiz o'chirilsa, qayta tiklab bo'lmaydi. Hisobingizga endi "
          "kira olmaysiz. Davom etasizmi?",
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Bekor qilish'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.neg),
            child: const Text("O'chirish"),
          ),
        ],
      ),
    );
    if (firstConfirm != true || !context.mounted) return;

    // Step 2: double confirm + the actual request runs inside this dialog so
    // there is no separate progress dialog left dangling after navigation.
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        bool isDeleting = false;
        String? error;
        return StatefulBuilder(
          builder: (ctx, setState) => AlertDialog(
            title: const Text('Tasdiqlash'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text("Rostan ham hisobingizni o'chirmoqchimisiz?"),
                if (error != null) ...[
                  const SizedBox(height: 12),
                  InlineError(message: error!),
                ],
              ],
            ),
            actions: [
              TextButton(
                onPressed: isDeleting ? null : () => Navigator.pop(ctx),
                child: const Text("Yo'q"),
              ),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.neg,
                  foregroundColor: Colors.white,
                ),
                onPressed: isDeleting
                    ? null
                    : () async {
                        setState(() {
                          isDeleting = true;
                          error = null;
                        });
                        try {
                          await ref
                              .read(authProvider.notifier)
                              .deleteAccount();
                          // Tokens cleared + auth state unauthenticated, so the
                          // router navigates to login. Close this dialog and
                          // report via the root messenger so the message
                          // survives the route change.
                          if (ctx.mounted) Navigator.pop(ctx);
                          rootScaffoldMessengerKey.currentState?.showSnackBar(
                            const SnackBar(
                              content: Text("Hisobingiz o'chirildi"),
                              backgroundColor: AppColors.pos,
                            ),
                          );
                        } catch (e) {
                          // 403 demo / network / 500: session untouched, keep
                          // the dialog open with a readable message.
                          setState(() {
                            isDeleting = false;
                            error = parseApiError(e);
                          });
                        }
                      },
                child: isDeleting
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text("Ha, o'chirish"),
              ),
            ],
          ),
        );
      },
    );
  }
}

/// Profil kartasi — `redesign4/profile/profile.html`.
class _ProfileCard extends StatelessWidget {
  final String fullName;
  final String username;
  final String phone;

  const _ProfileCard({
    required this.fullName,
    required this.username,
    required this.phone,
  });

  String get _initials {
    final source = fullName.trim().isNotEmpty ? fullName.trim() : username;
    if (source.isEmpty) return 'M';
    final parts = source.split(RegExp(r'\s+'));
    final letters = parts
        .where((p) => p.isNotEmpty)
        .take(2)
        .map((p) => p[0].toUpperCase())
        .join();
    return letters.isEmpty ? 'M' : letters;
  }

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.all(AppSpacing.s4),
      child: Row(
        children: [
          Container(
            width: 52,
            height: 52,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.action,
              borderRadius: BorderRadius.circular(14),
            ),
            child: Text(
              _initials,
              style: const TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.w800,
                color: AppColors.onAction,
              ),
            ),
          ),
          const SizedBox(width: AppSpacing.s4),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  fullName.isNotEmpty ? fullName : username,
                  style: AppText.bodyLg,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  phone.isNotEmpty ? '@$username · $phone' : '@$username',
                  style: const TextStyle(
                    color: AppColors.ink3,
                    fontSize: 11.5,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingsSection extends StatelessWidget {
  final String title;
  final List<Widget> children;

  const _SettingsSection({required this.title, required this.children});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppSectionLabel(title),
        AppCard(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.s4),
          child: Column(children: children),
        ),
      ],
    );
  }
}

/// `.prow` — 15px vertikal padding, ostida hairline.
class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _SettingsTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      type: MaterialType.transparency,
      child: InkWell(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 15),
          decoration: const BoxDecoration(
            border: Border(bottom: BorderSide(color: AppColors.line)),
          ),
          child: Row(
            children: [
              Icon(icon, size: 20, color: AppColors.ink3),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: AppColors.ink,
                  ),
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

// Tema tanlash bo'limi vaqtincha o'chirilgan: dizayn tizimi hozircha faqat
// qorong'i (tokens.css da yorug' palitra yo'q). Kelajakda ikkinchi palitra
// qo'shilganda quyidagi blokni va yuqoridagi `_ThemeSection()` chaqiruvini
// hamda `theme_provider.dart` importini qaytaring.
//
// class _ThemeSection extends ConsumerWidget {
//   @override
//   Widget build(BuildContext context, WidgetRef ref) {
//     final notifier = ref.read(themeModeProvider.notifier);
//
//     const options = [
//       (label: 'Tizim', value: 'system', icon: Icons.brightness_auto),
//       (label: 'Kunduzgi', value: 'light', icon: Icons.light_mode_outlined),
//       (label: 'Tungi', value: 'dark', icon: Icons.dark_mode_outlined),
//     ];
//
//     return Column(
//       crossAxisAlignment: CrossAxisAlignment.start,
//       children: [
//         const Padding(
//           padding: EdgeInsets.fromLTRB(4, 0, 0, 8),
//           child: Text(
//             'KO\'RINISH',
//             style: TextStyle(
//               color: AppColors.textSecondary,
//               fontSize: 12,
//               fontWeight: FontWeight.w600,
//               letterSpacing: 1.1,
//             ),
//           ),
//         ),
//         Card(
//           child: Padding(
//             padding: const EdgeInsets.all(16),
//             child: Column(
//               crossAxisAlignment: CrossAxisAlignment.start,
//               children: [
//                 const Text('Mavzu'),
//                 const SizedBox(height: 12),
//                 Row(
//                   children: options.map((opt) {
//                     final selected = notifier.currentThemeString == opt.value;
//                     return Expanded(
//                       child: GestureDetector(
//                         onTap: () async {
//                           await notifier.setFromServer(opt.value);
//                           await ref
//                               .read(profileActionProvider.notifier)
//                               .updateTheme(opt.value);
//                         },
//                         child: Container(
//                           margin: const EdgeInsets.symmetric(horizontal: 4),
//                           padding: const EdgeInsets.symmetric(vertical: 12),
//                           decoration: BoxDecoration(
//                             color: selected
//                                 ? AppColors.primary.withValues(alpha: 0.15)
//                                 : null,
//                             border: Border.all(
//                               color: selected
//                                   ? AppColors.primary
//                                   : AppColors.textSecondary.withValues(
//                                       alpha: 0.3,
//                                     ),
//                             ),
//                             borderRadius: BorderRadius.circular(8),
//                           ),
//                           child: Column(
//                             children: [
//                               Icon(
//                                 opt.icon,
//                                 color: selected
//                                     ? AppColors.primary
//                                     : AppColors.textSecondary,
//                                 size: 22,
//                               ),
//                               const SizedBox(height: 4),
//                               Text(
//                                 opt.label,
//                                 style: TextStyle(
//                                   fontSize: 12,
//                                   color: selected
//                                       ? AppColors.primary
//                                       : AppColors.textSecondary,
//                                   fontWeight: selected
//                                       ? FontWeight.w600
//                                       : FontWeight.normal,
//                                 ),
//                               ),
//                             ],
//                           ),
//                         ),
//                       ),
//                     );
//                   }).toList(),
//                 ),
//               ],
//             ),
//           ),
//         ),
//       ],
//     );
//   }
// }

class _BranchSection extends StatelessWidget {
  final dynamic user;

  const _BranchSection({required this.user});

  @override
  Widget build(BuildContext context) {
    if (user?.branches == null || (user.branches as List).isEmpty) {
      return const SizedBox.shrink();
    }

    final branches = user.branches as List;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const AppSectionLabel('Filiallar'),
        AppCard(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.s4),
          child: Column(
            children: [
              for (var i = 0; i < branches.length; i++)
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 15),
                  decoration: BoxDecoration(
                    border: i == branches.length - 1
                        ? null
                        : const Border(
                            bottom: BorderSide(color: AppColors.line),
                          ),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.store_outlined,
                        size: 20,
                        color: AppColors.ink3,
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Text(
                          branches[i].name as String,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                            color: AppColors.ink,
                          ),
                        ),
                      ),
                      AppTag(
                        label: branches[i].role as String,
                        color: AppColors.ink2,
                        size: AppTagSize.status,
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

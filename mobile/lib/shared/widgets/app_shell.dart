import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/profile/data/models/user_model.dart';
import 'grace_banner.dart';

final appShellScaffoldKey = GlobalKey<ScaffoldState>();

class AppShell extends ConsumerWidget {
  final Widget child;

  const AppShell({super.key, required this.child});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final showBanner = ref.watch(graceBannerVisibleProvider);

    return Scaffold(
      key: appShellScaffoldKey,
      drawer: _AppDrawer(user: user, ref: ref),
      // The grace banner sits above the page. Each page carries its own
      // Scaffold + AppBar, so when the banner is shown it consumes the top
      // safe area and we strip the page's duplicate top inset to keep the
      // AppBar flush beneath it. When hidden, the layout is untouched.
      body: showBanner
          ? Column(
              children: [
                const SafeArea(bottom: false, child: GraceBanner()),
                Expanded(
                  child: MediaQuery.removePadding(
                    context: context,
                    removeTop: true,
                    child: child,
                  ),
                ),
              ],
            )
          : child,
    );
  }
}

/// Yon menyu — `redesign4/drawer.html`.
///
/// ⚠️ Rol mantig'i (`showFull`, `showPhones`, ...), yo'llar va yorliqlar
/// o'zgarmadi — faqat ko'rinish qayta ishlandi.
class _AppDrawer extends StatelessWidget {
  final UserModel? user;
  final WidgetRef ref;

  const _AppDrawer({this.user, required this.ref});

  @override
  Widget build(BuildContext context) {
    final loc = GoRouterState.of(context).matchedLocation;
    final isOwner = user?.isOwner ?? false;
    final isPhoneSeller = user?.isPhoneSeller ?? false;
    final isAccessorySeller = user?.isAccessorySeller ?? false;
    final showFull = isOwner || isPhoneSeller || isAccessorySeller;

    final showPhones = isOwner || isPhoneSeller;
    final showAccessories = isOwner || isAccessorySeller;
    final showExtraProfit = isOwner || isPhoneSeller;
    final showSalaryCreate = isOwner;

    return Drawer(
      width: 308,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(),
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _DrawerHeader(user: user),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: AppSpacing.s2,
                ),
                children: [
                  if (showFull) ...[
                    const _SectionLabel('Dashboard'),
                    _DrawerItem(
                      icon: Icons.dashboard_outlined,
                      label: 'Dashboard',
                      path: '/dashboard',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/dashboard');
                      },
                    ),
                  ],
                  if (showPhones) ...[
                    const _SectionLabel('Telefonlar'),
                    _DrawerItem(
                      icon: Icons.phone_android,
                      label: 'Sotilmagan telefonlar',
                      path: '/phones/unsold',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/phones/unsold');
                      },
                    ),
                    _DrawerItem(
                      icon: Icons.sell_outlined,
                      label: 'Sotilgan telefonlar',
                      path: '/phones/sold',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/phones/sold');
                      },
                    ),
                  ],
                  if (showAccessories) ...[
                    const _SectionLabel('Aksessuarlar'),
                    _DrawerItem(
                      icon: Icons.cable_outlined,
                      label: 'Ombordagi aksessuarlar',
                      path: '/accessories/unsold',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/accessories/unsold');
                      },
                    ),
                    _DrawerItem(
                      icon: Icons.receipt_long_outlined,
                      label: 'Sotilgan aksessuarlar',
                      path: '/accessories/sold',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/accessories/sold');
                      },
                    ),
                  ],
                  if (showFull) ...[
                    const _SectionLabel('Qarzlar'),
                    _DrawerItem(
                      icon: Icons.account_balance_wallet_outlined,
                      label: 'Qarzlar',
                      path: '/debts/unpaid',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/debts/unpaid');
                      },
                    ),
                    _DrawerItem(
                      icon: Icons.check_circle_outline,
                      label: "To'langan qarzlar",
                      path: '/debts/closed',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/debts/closed');
                      },
                    ),
                    const _SectionLabel('Xarajatlar'),
                    _DrawerItem(
                      icon: Icons.receipt_outlined,
                      label: 'Xarajatlar',
                      path: '/expenses',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/expenses');
                      },
                    ),
                    const _SectionLabel('Oyliklar'),
                    _DrawerItem(
                      icon: Icons.payments_outlined,
                      label: showSalaryCreate ? 'Oyliklar' : 'Mening oyligim',
                      path: '/salaries',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/salaries');
                      },
                    ),
                  ],
                  if (showExtraProfit) ...[
                    const _SectionLabel("Qo'shimcha foyda"),
                    _DrawerItem(
                      icon: Icons.trending_up_outlined,
                      label: "Qo'shimcha foyda",
                      path: '/extra-profits',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/extra-profits');
                      },
                    ),
                  ],
                  if (isOwner) ...[
                    const _SectionLabel('Kapital'),
                    _DrawerItem(
                      icon: Icons.phone_android_outlined,
                      label: 'Telefon kapitali',
                      path: '/capital/phone',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/capital/phone');
                      },
                    ),
                    _DrawerItem(
                      icon: Icons.cable_outlined,
                      label: 'Aksessuar kapitali',
                      path: '/capital/accessory',
                      current: loc,
                      onTap: () {
                        Navigator.of(context).pop();
                        context.go('/capital/accessory');
                      },
                    ),
                  ],
                ],
              ),
            ),
            // `.dw-foot` — yuqorisida hairline, pastida 14px.
            Container(height: 1, color: AppColors.line),
            Padding(
              padding: const EdgeInsets.fromLTRB(10, AppSpacing.s2, 10, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _DrawerItem(
                    icon: Icons.support_agent_outlined,
                    label: 'Yordam va murojaat',
                    path: '/support',
                    current: loc,
                    onTap: () {
                      Navigator.of(context).pop();
                      context.go('/support');
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.person_outline,
                    label: 'Sozlamalar / Profil',
                    path: '/profile',
                    current: loc,
                    onTap: () {
                      Navigator.of(context).pop();
                      context.go('/profile');
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.logout,
                    label: 'Chiqish',
                    path: '',
                    current: loc,
                    onTap: () async {
                      Navigator.of(context).pop();
                      await ref.read(authProvider.notifier).logout();
                    },
                    color: AppColors.neg,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// `.dw-head` — avatar (bosh harflar), ism, "@login · rol · filial".
class _DrawerHeader extends StatelessWidget {
  final UserModel? user;

  const _DrawerHeader({this.user});

  /// To'liq ismdan bosh harflarni oladi (dizaynda "ST", "AK", "NY").
  String get _initials {
    final source = (user?.fullName.trim().isNotEmpty ?? false)
        ? user!.fullName.trim()
        : (user?.username.trim() ?? '');
    if (source.isEmpty) return 'M';
    final parts = source.split(RegExp(r'\s+'));
    final letters = parts
        .where((p) => p.isNotEmpty)
        .take(2)
        .map((p) => p[0].toUpperCase())
        .join();
    return letters.isEmpty ? 'M' : letters;
  }

  /// "@sardor · Owner · Chilonzor filiali" — barchasi mavjud `UserModel`
  /// maydonlaridan olinadi, yangi ma'lumot so'ralmaydi.
  String get _subtitle {
    final parts = <String>[];
    final username = user?.username ?? '';
    if (username.isNotEmpty) parts.add('@$username');

    if (user != null) {
      if (user!.isOwner) {
        parts.add('Owner');
      } else if (user!.isPhoneSeller) {
        parts.add('Telefon sotuvchi');
      } else if (user!.isAccessorySeller) {
        parts.add('Aksessuar sotuvchi');
      }

      final branches = user!.branches;
      if (branches.length == 1) {
        parts.add(branches.first.name);
      } else if (branches.length > 1) {
        parts.add('${branches.length} filial');
      }
    }

    return parts.join(' · ');
  }

  @override
  Widget build(BuildContext context) {
    final name = (user?.fullName.isNotEmpty ?? false)
        ? user!.fullName
        : (user?.username ?? 'Mobirex');
    final subtitle = _subtitle;

    return Container(
      padding: const EdgeInsets.fromLTRB(20, 22, 20, AppSpacing.s4),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.line)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
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
          const SizedBox(height: 10),
          Text(
            name,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: AppColors.ink,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          if (subtitle.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                subtitle,
                style: const TextStyle(
                  fontSize: 11.5,
                  color: AppColors.ink3,
                ),
                maxLines: 2,
              ),
            ),
        ],
      ),
    );
  }
}

/// `.dw-sect` — 9.5px · 800 · UPPERCASE · ls +0.14em.
class _SectionLabel extends StatelessWidget {
  final String label;

  const _SectionLabel(this.label);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(10, 14, 10, 6),
      child: Text(label.toUpperCase(), style: AppText.micro),
    );
  }
}

/// `.dw-item` — 44px · 10px radius · faol holatda `--card` fon va
/// `--action` ikon.
class _DrawerItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String path;
  final String current;
  final VoidCallback onTap;
  final Color? color;

  const _DrawerItem({
    required this.icon,
    required this.label,
    required this.path,
    required this.current,
    required this.onTap,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final isActive = path.isNotEmpty && current.startsWith(path);
    final Color textColor =
        color ?? (isActive ? AppColors.ink : AppColors.ink2);
    final Color iconColor =
        color ?? (isActive ? AppColors.action : AppColors.ink3);

    return Material(
      type: MaterialType.transparency,
      child: InkWell(
        onTap: onTap,
        borderRadius: AppRadius.inputRadius,
        child: Container(
          height: 44,
          padding: const EdgeInsets.symmetric(horizontal: 10),
          decoration: BoxDecoration(
            color: isActive ? AppColors.card : Colors.transparent,
            borderRadius: AppRadius.inputRadius,
          ),
          child: Row(
            children: [
              Icon(icon, size: 18, color: iconColor),
              const SizedBox(width: AppSpacing.s3),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: textColor,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

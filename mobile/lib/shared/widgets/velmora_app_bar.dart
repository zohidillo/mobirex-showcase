import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/theme/app_theme.dart';
import 'app_shell.dart';

/// Header bloki — `redesign3/unsold-phones.html` `.hdr`.
///
/// Surface fon, pastki burchaklari 16px, BITTA soya, ro'yxat ustida turadi.
/// Ierarxiya teskari aylantirildi: endi ekran nomi katta (20px/750), brend
/// esa kichkina ostki qator ("Mobirex").
///
/// Konstruktor imzosi o'zgarmadi — `subtitle` hamon ekran nomini oladi
/// (endi u KATTA qator sifatida ko'rsatiladi), shuning uchun 21 ta call site
/// tegilmasdan ishlayveradi.
///
/// Qidiruv qatori yoki filtr paneli kerak bo'lsa — [bottom] ga bering
/// (masalan [AppSearchBar]); balandlik avtomatik hisoblanadi.
class VelmoraAppBar extends StatelessWidget implements PreferredSizeWidget {
  const VelmoraAppBar({
    super.key,
    this.subtitle,
    this.actions = const [],
    this.showDrawer = false,
    this.onBack,
    this.caption = 'Mobirex',
    this.bottom,
  });

  /// Ekran nomi — dizaynda `.htitle .h` (20px/750).
  final String? subtitle;

  /// O'ng tomondagi tugmalar.
  final List<Widget> actions;

  /// Chapda drawer tugmasi (aks holda orqaga tugmasi yoki bo'sh).
  final bool showDrawer;

  final VoidCallback? onBack;

  /// Sarlavha ostidagi kichik qator — dizaynda `.htitle .s`.
  final String? caption;

  /// Header ichiga qo'shiladigan qism: qidiruv qatori, filtr paneli.
  final PreferredSizeWidget? bottom;

  /// `.hdr` = padding 10 + `.hdr-top` 52 + padding 14.
  static const double _baseHeight = 76;

  @override
  Size get preferredSize =>
      Size.fromHeight(_baseHeight + (bottom?.preferredSize.height ?? 0));

  @override
  Widget build(BuildContext context) {
    Widget? leading;
    if (showDrawer) {
      leading = AppHeaderButton(
        icon: Icons.menu,
        onPressed: () => appShellScaffoldKey.currentState?.openDrawer(),
      );
    } else if (onBack != null) {
      leading = AppHeaderButton(icon: Icons.arrow_back, onPressed: onBack);
    } else if (Navigator.of(context).canPop()) {
      leading = AppHeaderButton(
        icon: Icons.arrow_back,
        onPressed: () => Navigator.of(context).maybePop(),
      );
    }

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light.copyWith(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
        statusBarBrightness: Brightness.dark,
      ),
      child: Container(
        decoration: const BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.vertical(
            bottom: Radius.circular(AppRadius.block),
          ),
          boxShadow: AppShadows.card,
        ),
        child: SafeArea(
          bottom: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 14),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ConstrainedBox(
                  constraints: const BoxConstraints(minHeight: 52),
                  child: Row(
                    children: [
                      if (leading != null) ...[
                        leading,
                        const SizedBox(width: 6),
                      ],
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (subtitle != null && subtitle!.isNotEmpty)
                              Text(
                                subtitle!,
                                style: AppText.title,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            if (caption != null && caption!.isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 1),
                                child: Text(
                                  caption!,
                                  style: const TextStyle(
                                    fontSize: 11.5,
                                    color: AppColors.ink3,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                          ],
                        ),
                      ),
                      for (final action in actions) ...[
                        const SizedBox(width: 6),
                        action,
                      ],
                    ],
                  ),
                ),
                ?bottom,
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Header ichidagi ikon tugmasi — `.hbtn` (42×42, 12px radius).
class AppHeaderButton extends StatelessWidget {
  const AppHeaderButton({
    super.key,
    required this.icon,
    this.onPressed,
    this.tooltip,
    this.isActive = false,
  });

  final IconData icon;
  final VoidCallback? onPressed;
  final String? tooltip;

  /// Faol holat — ikon `--action` rangida.
  final bool isActive;

  @override
  Widget build(BuildContext context) {
    final button = Material(
      type: MaterialType.transparency,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(AppRadius.card),
        highlightColor: AppColors.cardPressed,
        child: SizedBox(
          width: 42,
          height: 42,
          child: Icon(
            icon,
            size: 22,
            color: isActive ? AppColors.action : AppColors.ink2,
          ),
        ),
      ),
    );

    if (tooltip == null) return button;
    return Tooltip(message: tooltip!, child: button);
  }
}

/// Qidiruv + filtr bitta bar — `.searchbar`.
///
/// 48px balandlik · `--card` fon · 1.5px shaffof chegara (fokusda `--action`)
/// · o'ngda tozalash (matn bo'lsa) va filtr tugmasi.
class AppSearchBar extends StatelessWidget implements PreferredSizeWidget {
  const AppSearchBar({
    super.key,
    required this.controller,
    this.hintText = '',
    this.onChanged,
    this.onClear,
    this.onFilterTap,
    this.isFilterActive = false,
    this.focusNode,
  });

  final TextEditingController controller;
  final String hintText;
  final ValueChanged<String>? onChanged;

  /// `null` bo'lsa tozalash tugmasi umuman ko'rsatilmaydi.
  final VoidCallback? onClear;

  /// `null` bo'lsa filtr tugmasi ko'rsatilmaydi.
  final VoidCallback? onFilterTap;

  /// Filtr qo'llangan bo'lsa ikon `--action` rangida.
  final bool isFilterActive;

  final FocusNode? focusNode;

  /// 6px yuqori bo'shliq + 48px bar.
  @override
  Size get preferredSize => const Size.fromHeight(54);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 6),
      child: SizedBox(
        height: 48,
        child: ValueListenableBuilder<TextEditingValue>(
          valueListenable: controller,
          builder: (context, value, _) {
            final hasText = value.text.isNotEmpty;
            return Container(
              padding: const EdgeInsets.only(left: 14, right: 4),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: AppRadius.inputRadius,
              ),
              child: Row(
                children: [
                  const Icon(Icons.search, size: 18, color: AppColors.ink3),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextField(
                      controller: controller,
                      focusNode: focusNode,
                      onChanged: onChanged,
                      style: AppText.body,
                      cursorColor: AppColors.action,
                      textAlignVertical: TextAlignVertical.center,
                      decoration: InputDecoration(
                        isCollapsed: true,
                        filled: false,
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        hintText: hintText,
                        hintStyle: AppText.body.copyWith(
                          color: AppColors.ink3,
                        ),
                        contentPadding: EdgeInsets.zero,
                      ),
                    ),
                  ),
                  if (hasText && onClear != null)
                    _SearchIconButton(
                      icon: Icons.close,
                      color: AppColors.ink3,
                      iconSize: 18,
                      onTap: onClear!,
                    ),
                  if (onFilterTap != null) ...[
                    Container(
                      width: 1,
                      height: 24,
                      margin: const EdgeInsets.symmetric(horizontal: 4),
                      color: AppColors.line,
                    ),
                    _SearchIconButton(
                      icon: Icons.tune,
                      color: isFilterActive
                          ? AppColors.action
                          : AppColors.ink2,
                      onTap: onFilterTap!,
                    ),
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _SearchIconButton extends StatelessWidget {
  const _SearchIconButton({
    required this.icon,
    required this.color,
    required this.onTap,
    this.iconSize = 22,
  });

  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final double iconSize;

  @override
  Widget build(BuildContext context) {
    return Material(
      type: MaterialType.transparency,
      child: InkWell(
        onTap: onTap,
        borderRadius: AppRadius.chipRadius,
        // 44×44 — Apple minimal tegish maydoni. Faqat tegish zonasi
        // kattalashdi, `iconSize` o'zgarmadi (48px bar ichiga sig'adi).
        child: SizedBox(
          width: 44,
          height: 44,
          child: Icon(icon, size: iconSize, color: color),
        ),
      ),
    );
  }
}

/// Filtr paneli — `.fpanel` (pill dropdownlar qatori).
///
/// [VelmoraAppBar.bottom] ichida [AppSearchBar] bilan birga ishlatiladi.
class AppFilterPanel extends StatelessWidget implements PreferredSizeWidget {
  const AppFilterPanel({super.key, required this.children});

  final List<Widget> children;

  /// 12px yuqori bo'shliq + 38px pill.
  @override
  Size get preferredSize => const Size.fromHeight(50);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.s3),
      child: SizedBox(
        height: 38,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: children.length,
          separatorBuilder: (_, _) => const SizedBox(width: AppSpacing.s2),
          itemBuilder: (_, i) => children[i],
        ),
      ),
    );
  }
}

/// [AppSearchBar] va [AppFilterPanel] ni bitta `bottom` ga birlashtiradi.
class AppHeaderBottom extends StatelessWidget implements PreferredSizeWidget {
  const AppHeaderBottom({super.key, required this.children});

  final List<PreferredSizeWidget> children;

  @override
  Size get preferredSize => Size.fromHeight(
    children.fold(0, (sum, w) => sum + w.preferredSize.height),
  );

  @override
  Widget build(BuildContext context) {
    return Column(mainAxisSize: MainAxisSize.min, children: children);
  }
}

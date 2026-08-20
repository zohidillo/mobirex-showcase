import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Olib tashlanadigan faol filtr chipi — `tokens.css` `.chip`.
///
/// 34px balandlik · card fon · 1px `--line-strong` chegara · 8px radius ·
/// o'ngida 24×24 yopish tugmasi.
class AppFilterChip extends StatelessWidget {
  const AppFilterChip({super.key, required this.label, this.onRemove});

  final String label;

  /// `null` bo'lsa yopish tugmasi ko'rsatilmaydi.
  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 34,
      padding: EdgeInsets.only(left: 12, right: onRemove == null ? 12 : 6),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: AppRadius.chipRadius,
        border: Border.all(color: AppColors.lineStrong),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppColors.ink,
            ),
          ),
          if (onRemove != null) ...[
            const SizedBox(width: AppSpacing.s2),
            _RemoveButton(onTap: onRemove!),
          ],
        ],
      ),
    );
  }
}

class _RemoveButton extends StatelessWidget {
  const _RemoveButton({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      type: MaterialType.transparency,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(6),
        // Tegish maydoni chip'ning to'liq balandligiga (34px) kengaytirildi.
        // 44px ga chiqarish uchun chip'ning o'zini kattalashtirish kerak
        // bo'lardi — u esa `.chip` tokeni (34px), shuning uchun tegilmadi.
        child: const SizedBox(
          width: 34,
          height: 34,
          child: Icon(Icons.close, size: 14, color: AppColors.ink3),
        ),
      ),
    );
  }
}

/// Filtr paneli pill'i — `.fdrop` / `.fdrop.set`.
///
/// Yopiq holat: card fon, `--ink-3` matn. Tanlangan (`set`): `--ink` matn,
/// 600 vazn, `--line-strong` chegara. Ochiq holat: aksent chegara va matn.
class AppFilterDropdown extends StatelessWidget {
  const AppFilterDropdown({
    super.key,
    required this.label,
    this.onTap,
    this.isSet = false,
    this.isOpen = false,
  });

  final String label;
  final VoidCallback? onTap;

  /// Qiymat tanlanganmi.
  final bool isSet;

  /// Tanlash oynasi ochiqmi.
  final bool isOpen;

  @override
  Widget build(BuildContext context) {
    final Color fg = isOpen
        ? AppColors.action
        : (isSet ? AppColors.ink : AppColors.ink3);
    final Color? border = isOpen
        ? AppColors.action
        : (isSet ? AppColors.lineStrong : null);

    return Material(
      type: MaterialType.transparency,
      child: InkWell(
        onTap: onTap,
        borderRadius: AppRadius.chipRadius,
        child: Container(
          height: 38,
          padding: const EdgeInsets.symmetric(horizontal: 13),
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: AppRadius.chipRadius,
            border: border == null ? null : Border.all(color: border),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                label,
                style: TextStyle(
                  fontSize: 12.5,
                  fontWeight: isSet ? FontWeight.w600 : FontWeight.w500,
                  color: fg,
                ),
              ),
              const SizedBox(width: AppSpacing.s2),
              Icon(
                isOpen ? Icons.expand_less : Icons.expand_more,
                size: 14,
                color: fg,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Brend belgisi — `redesign3/login.html` `.lg-brand` / `.lg-wm` / `.lg-tag`.
///
/// Geometriya mokapning `.mono` qoidasidan olingan (88×88, radius =
/// o'lcham × 0.25, `--shadow-card`), lekin ichida HAQIQIY PNG logotip
/// turadi — matn monogrammasi emas.
///
/// Mokapda monogramma ishlatilgani HTML'da PNG bo'lmagani uchun edi, dizayn
/// qarori emas: `MR` belgisi brend aktivi bo'lib, App Store ikonkasi ham
/// o'sha fayl. Monogramma faqat `errorBuilder` zaxirasi sifatida qoldi.
class MobirexLogo extends StatelessWidget {
  /// Brend aktivi. `pubspec.yaml` dagi `flutter: assets:` da e'lon qilingan.
  static const assetPath = 'assets/images/mobirex_logo.png';

  final double size;

  /// "Mobirex" so'z-belgisini ko'rsatish.
  final bool showText;

  /// Slogan qatorini ko'rsatish (`.lg-tag`).
  final bool showTagline;

  const MobirexLogo({
    super.key,
    this.size = 96,
    this.showText = false,
    this.showTagline = false,
  });

  /// Asset topilmasa ko'rsatiladigan zaxira — mokapdagi `.mono` monogrammasi.
  ///
  /// Hech qachon bo'sh joy yoki xato ekrani qoldirmaydi.
  Widget _monogramFallback() {
    return Container(
      width: size,
      height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppColors.action,
        borderRadius: BorderRadius.circular(size * 0.25),
      ),
      child: Text(
        'MR',
        style: TextStyle(
          fontSize: size * 0.375,
          fontWeight: FontWeight.w800,
          letterSpacing: size * -0.02,
          color: AppColors.onAction,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(size * 0.25);

    // Semantics tashqarida: `Image.asset` ning `errorBuilder` yo'li o'zining
    // Semantics o'ramasidan OLDIN return qiladi (SDK image.dart), shuning
    // uchun `semanticLabel` faqat rasm yuklanganda ishlardi. Bu yerda o'rash
    // zaxira monogramma ham nomlanishini kafolatlaydi.
    final logo = Semantics(
      image: true,
      label: 'Mobirex',
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          borderRadius: radius,
          boxShadow: AppShadows.card,
        ),
        child: ClipRRect(
          borderRadius: radius,
          child: Image.asset(
            assetPath,
            width: size,
            height: size,
            fit: BoxFit.cover,
            filterQuality: FilterQuality.medium,
            excludeFromSemantics: true,
            errorBuilder: (context, error, stackTrace) => _monogramFallback(),
          ),
        ),
      ),
    );

    if (!showText && !showTagline) return logo;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        logo,
        if (showText)
          const Padding(
            padding: EdgeInsets.only(top: AppSpacing.s5),
            child: Text(
              'Mobirex',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.96,
                color: AppColors.ink,
              ),
            ),
          ),
        if (showTagline)
          const Padding(
            padding: EdgeInsets.only(top: 7),
            child: Text(
              'Telefon va aksessuar do‘konlari uchun CRM',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12.5, color: AppColors.ink2),
            ),
          ),
      ],
    );
  }
}

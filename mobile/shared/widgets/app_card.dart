import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Kartaning chap qirrasi — `tokens.css` `.card` / `.card.pos` / `.card.neg`.
enum AppCardEdge {
  /// `--edge-neutral` — odatiy holat.
  neutral,

  /// `--pos` — musbat (biz berdik, foyda).
  positive,

  /// `--neg` — manfiy (biz oldik, xarajat).
  negative,
}

/// Tizimdagi YAGONA ro'yxat kartasi — `redesign3/unsold-phones.html` `.card`.
///
/// Anatomiyasi: bitta fill + 12px radius + BITTA soya + 2px chap qirra.
/// Bosilganda fill bir pog'ona ochiladi va karta 1px pastga suriladi (120ms).
///
/// Sahifa fayllarida `BoxDecoration` bilan qo'lda karta YASAMANG — shu
/// widgetni ishlating.
class AppCard extends StatefulWidget {
  const AppCard({
    super.key,
    required this.child,
    this.onTap,
    this.onLongPress,
    this.edge = AppCardEdge.neutral,
    this.padding = const EdgeInsets.fromLTRB(15, 14, 16, 14),
  });

  final Widget child;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;
  final AppCardEdge edge;
  final EdgeInsetsGeometry padding;

  @override
  State<AppCard> createState() => _AppCardState();
}

class _AppCardState extends State<AppCard> {
  bool _pressed = false;

  void _setPressed(bool value) {
    if (_pressed == value) return;
    setState(() => _pressed = value);
  }

  Color get _edgeColor => switch (widget.edge) {
    AppCardEdge.neutral => AppColors.edgeNeutral,
    AppCardEdge.positive => AppColors.pos,
    AppCardEdge.negative => AppColors.neg,
  };

  @override
  Widget build(BuildContext context) {
    final interactive = widget.onTap != null || widget.onLongPress != null;
    final pressed = interactive && _pressed;

    return AnimatedContainer(
      duration: AppDurations.press,
      curve: AppCurves.press,
      transform: Matrix4.translationValues(0, pressed ? 1 : 0, 0),
      decoration: BoxDecoration(
        color: pressed ? AppColors.cardPressed : AppColors.card,
        borderRadius: AppRadius.cardRadius,
        boxShadow: pressed ? AppShadows.cardPressed : AppShadows.card,
      ),
      child: ClipRRect(
        borderRadius: AppRadius.cardRadius,
        child: Material(
          type: MaterialType.transparency,
          child: InkWell(
            onTap: widget.onTap,
            onLongPress: widget.onLongPress,
            onHighlightChanged: _setPressed,
            // Dizaynda ripple yo'q — javob fill + 1px siljish orqali beriladi.
            splashColor: Colors.transparent,
            highlightColor: Colors.transparent,
            hoverColor: Colors.transparent,
            // 2px chap qirra `Border` orqali chiziladi, `Row` + `stretch`
            // orqali EMAS: ro'yxat (`ListView`) bolasiga balandlikni cheksiz
            // beradi, `stretch` esa shu cheksizlikni bolaga tight qilib
            // uzatib, "BoxConstraints forces an infinite height" ga olib
            // kelardi (release'da karta umuman ko'rinmasdi).
            // `Container` chegara qalinligini bolaning padding'iga qo'shadi,
            // shuning uchun chap bo'shliq avvalgidek 2 + padding.left.
            child: Container(
              decoration: BoxDecoration(
                border: Border(
                  left: BorderSide(color: _edgeColor, width: 2),
                ),
              ),
              padding: widget.padding,
              child: widget.child,
            ),
          ),
        ),
      ),
    );
  }
}

/// Kartaning hero qiymati — `.hero` (28/800 tabular) va ixtiyoriy
/// `.hero small` qo'shimchasi (12/500 `--ink-3`).
class AppHeroValue extends StatelessWidget {
  const AppHeroValue({super.key, required this.value, this.suffix, this.color});

  final String value;

  /// Masalan "foyda $80" yoki "jami $450".
  final String? suffix;

  /// `--pos` / `--neg`; `null` bo'lsa `--ink`.
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final style = color == null
        ? AppText.display
        : AppText.display.copyWith(color: color);

    if (suffix == null || suffix!.isEmpty) {
      return Text(value, style: style, maxLines: 1);
    }

    return Text.rich(
      TextSpan(
        text: value,
        style: style,
        children: [
          TextSpan(
            text: ' $suffix',
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              letterSpacing: 0,
              color: AppColors.ink3,
            ),
          ),
        ],
      ),
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
    );
  }
}

/// Yuklanish holatidagi yassi skeleton karta — `.skel`.
///
/// Animatsiya YO'Q (perf qoidasi): faqat statik bloklar.
class AppCardSkeleton extends StatelessWidget {
  const AppCardSkeleton({
    super.key,
    this.lineWidths = const [0.55, 0.38, 0.75],
  });

  /// Har bir chiziqning kenglik ulushi (0..1). Ikkinchisi hero qatori —
  /// balandligi 22px, qolganlari 12px va 9px.
  final List<double> lineWidths;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.card,
        borderRadius: AppRadius.cardRadius,
      ),
      child: ClipRRect(
        borderRadius: AppRadius.cardRadius,
        // [AppCard] bilan bir xil sabab — `Row` + `stretch` emas, `Border`.
        child: Container(
          decoration: const BoxDecoration(
            border: Border(
              left: BorderSide(color: AppColors.edgeNeutral, width: 2),
            ),
          ),
          padding: const EdgeInsets.all(AppSpacing.s4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var i = 0; i < lineWidths.length; i++) ...[
                if (i > 0) const SizedBox(height: 10),
                FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: lineWidths[i].clamp(0.0, 1.0),
                  child: Container(
                    height: switch (i) {
                      1 => 22.0,
                      2 => 9.0,
                      _ => 12.0,
                    },
                    decoration: BoxDecoration(
                      color: AppColors.cardPressed,
                      borderRadius: BorderRadius.circular(6),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

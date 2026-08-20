import 'dart:math';
import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../data/models/dashboard_model.dart';

/// Sotuv grafigi — `redesign3/staff-dashboard.html` `.chartbox`.
///
/// ⚠️ Chizish mantig'i va ma'lumot moslashuvi o'zgarmadi — faqat ranglar:
/// ustunlar `--edge-neutral`, eng yuqori kun `--action`, to'r chiziqlari
/// olib tashlandi (dizaynda yo'q).
class SalesChart extends StatelessWidget {
  final List<SalesSeriesModel> series;

  const SalesChart({super.key, required this.series});

  @override
  Widget build(BuildContext context) {
    if (series.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.s4,
          vertical: AppSpacing.s7,
        ),
        decoration: const BoxDecoration(
          color: AppColors.card,
          borderRadius: AppRadius.cardRadius,
          boxShadow: AppShadows.card,
        ),
        child: const Center(
          child: Text(
            'Bu oyda sotuv mavjud emas',
            style: TextStyle(color: AppColors.ink2, fontSize: 14),
          ),
        ),
      );
    }

    return Container(
      decoration: const BoxDecoration(
        color: AppColors.card,
        borderRadius: AppRadius.cardRadius,
        boxShadow: AppShadows.card,
      ),
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            height: 140,
            child: CustomPaint(
              painter: _BarChartPainter(
                series: series,
                barColor: AppColors.edgeNeutral,
                highlightColor: AppColors.action,
                textColor: AppColors.ink3,
              ),
              child: const SizedBox.expand(),
            ),
          ),
          const SizedBox(height: AppSpacing.s2),
          const Text(
            'Kunlik sotuv (so\'m) · eng yuqori kun aksentda',
            style: TextStyle(color: AppColors.ink3, fontSize: 10.5),
          ),
        ],
      ),
    );
  }
}

class _BarChartPainter extends CustomPainter {
  final List<SalesSeriesModel> series;
  final Color barColor;
  final Color highlightColor;
  final Color textColor;

  static const int _days = 31;
  static const double _bottomPadding = 22;
  static const double _topPadding = 8;
  static const double _leftPadding = 4;

  _BarChartPainter({
    required this.series,
    required this.barColor,
    required this.highlightColor,
    required this.textColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final maxAmount = series.map((s) => s.amount).reduce(max);
    if (maxAmount == 0) return;

    final chartHeight = size.height - _bottomPadding - _topPadding;
    final chartWidth = size.width - _leftPadding;
    final slotWidth = chartWidth / _days;
    final barWidth = (slotWidth * 0.65).clamp(3.0, 20.0);

    final barPaint = Paint()
      ..color = barColor
      ..style = PaintingStyle.fill;

    final highlightPaint = Paint()
      ..color = highlightColor
      ..style = PaintingStyle.fill;

    final textStyle = TextStyle(
      color: textColor,
      fontSize: 9,
      fontWeight: FontWeight.w500,
    );

    for (final s in series) {
      if (s.day < 1 || s.day > _days) continue;

      final slotX = _leftPadding + (s.day - 1) * slotWidth;
      final centerX = slotX + slotWidth / 2;
      final barHeight = (s.amount / maxAmount) * chartHeight;
      final barTop = _topPadding + chartHeight - barHeight;
      final barLeft = centerX - barWidth / 2;

      final rrect = RRect.fromRectAndRadius(
        Rect.fromLTWH(barLeft, barTop, barWidth, barHeight),
        const Radius.circular(3),
      );
      canvas.drawRRect(
        rrect,
        s.amount == maxAmount ? highlightPaint : barPaint,
      );

      // Day label
      final tp = TextPainter(
        text: TextSpan(text: '${s.day}', style: textStyle),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(
        canvas,
        Offset(centerX - tp.width / 2, _topPadding + chartHeight + 5),
      );
    }
  }

  @override
  bool shouldRepaint(_BarChartPainter old) => old.series != series;
}

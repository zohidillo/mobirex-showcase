import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

/// PIN klaviaturasi — `redesign4/auth/pin-verify.html` + `r4.css` PIN oilasi.
///
/// Nuqtalar 16px (`--line-strong` chegara, to'lganda `--action`), klaviatura
/// 3×72px doiralar (`--card`, bosilganda `--card-pressed` + 1px siljish).
///
/// ⚠️ Mantiq o'zgarmadi: `onCompleted`, `errorText`, `autoClear` va ichki
/// PIN yig'ish algoritmi avvalgidek.
class PinInputWidget extends StatefulWidget {
  final void Function(String pin) onCompleted;
  final String? errorText;
  final bool autoClear;

  /// Qolgan urinishlar soni. `null` bo'lsa ko'rsatilmaydi — provider bu
  /// ma'lumotni bermasa, hech narsa o'ylab topilmaydi.
  final int? attemptsRemaining;

  const PinInputWidget({
    super.key,
    required this.onCompleted,
    this.errorText,
    this.autoClear = false,
    this.attemptsRemaining,
  });

  @override
  State<PinInputWidget> createState() => _PinInputWidgetState();
}

class _PinInputWidgetState extends State<PinInputWidget> {
  String _pin = '';

  void _append(String digit) {
    if (_pin.length >= 4) return;
    setState(() => _pin += digit);
    if (_pin.length == 4) {
      widget.onCompleted(_pin);
      if (widget.autoClear) {
        Future.delayed(
          const Duration(milliseconds: 200),
          () => setState(() => _pin = ''),
        );
      }
    }
  }

  void _delete() {
    if (_pin.isEmpty) return;
    setState(() => _pin = _pin.substring(0, _pin.length - 1));
  }

  void clear() => setState(() => _pin = '');

  @override
  Widget build(BuildContext context) {
    final hasError = widget.errorText != null;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // `.pindots` — margin 28 0 8, gap 16.
        Padding(
          padding: const EdgeInsets.only(top: AppSpacing.s7, bottom: AppSpacing.s2),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(4, (i) {
              final filled = i < _pin.length;
              final Color on = hasError ? AppColors.neg : AppColors.action;
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: AppSpacing.s2),
                width: 16,
                height: 16,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: filled ? on : Colors.transparent,
                  border: Border.all(
                    color: hasError ? AppColors.neg : (filled ? on : AppColors.lineStrong),
                    width: 2,
                  ),
                ),
              );
            }),
          ),
        ),
        if (hasError)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              widget.errorText!,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.neg, fontSize: 12.5),
            ),
          ),
        if (widget.attemptsRemaining != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text.rich(
              TextSpan(
                text: 'Qolgan urinishlar: ',
                style: const TextStyle(fontSize: 12, color: AppColors.ink3),
                children: [
                  TextSpan(
                    text: '${widget.attemptsRemaining}',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: AppColors.warn,
                    ),
                  ),
                ],
              ),
            ),
          ),
        const SizedBox(height: AppSpacing.s6),
        _buildNumpad(),
      ],
    );
  }

  /// `.numpad` — 3 ustun, ustunlar orasi 26px, qatorlar orasi 14px.
  Widget _buildNumpad() {
    const rows = [
      ['1', '2', '3'],
      ['4', '5', '6'],
      ['7', '8', '9'],
    ];
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (final row in rows)
          Padding(
            padding: const EdgeInsets.only(bottom: 14),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                for (final d in row) _PinKey(label: d, onTap: () => _append(d)),
              ],
            ),
          ),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(width: 72 + 26),
            _PinKey(label: '0', onTap: () => _append('0')),
            _PinKey(icon: Icons.backspace_outlined, onTap: _delete),
          ],
        ),
      ],
    );
  }
}

/// `.numkey` — 72px doira, bosilganda `--card-pressed` + 1px siljish.
class _PinKey extends StatefulWidget {
  const _PinKey({this.label, this.icon, required this.onTap});

  final String? label;
  final IconData? icon;
  final VoidCallback onTap;

  @override
  State<_PinKey> createState() => _PinKeyState();
}

class _PinKeyState extends State<_PinKey> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    /// Ikonli tugma `.numkey.ghost` — foni yo'q.
    final isGhost = widget.icon != null;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 13),
      child: AnimatedContainer(
        duration: AppDurations.press,
        curve: AppCurves.press,
        width: 72,
        height: 72,
        transform: Matrix4.translationValues(0, _pressed ? 1 : 0, 0),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: _pressed
              ? AppColors.cardPressed
              : (isGhost ? Colors.transparent : AppColors.card),
        ),
        child: Material(
          type: MaterialType.transparency,
          child: InkWell(
            onTap: widget.onTap,
            customBorder: const CircleBorder(),
            onHighlightChanged: (v) {
              if (_pressed != v) setState(() => _pressed = v);
            },
            splashColor: Colors.transparent,
            highlightColor: Colors.transparent,
            child: Center(
              child: isGhost
                  ? Icon(widget.icon, size: 22, color: AppColors.ink2)
                  : Text(
                      widget.label!,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w700,
                        color: AppColors.ink,
                      ),
                    ),
            ),
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/pin_input_widget.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../providers/auth_provider.dart';

enum _PinChangeStep { enterOld, enterNew, confirmNew }

class PinChangePage extends ConsumerStatefulWidget {
  const PinChangePage({super.key});

  @override
  ConsumerState<PinChangePage> createState() => _PinChangePageState();
}

class _PinChangePageState extends ConsumerState<PinChangePage> {
  _PinChangeStep _step = _PinChangeStep.enterOld;
  String? _oldPin;
  String? _newPin;
  String? _error;
  bool _isLoading = false;

  Future<void> _onPinEntered(String pin) async {
    switch (_step) {
      case _PinChangeStep.enterOld:
        setState(() {
          _oldPin = pin;
          _step = _PinChangeStep.enterNew;
          _error = null;
        });
      case _PinChangeStep.enterNew:
        setState(() {
          _newPin = pin;
          _step = _PinChangeStep.confirmNew;
          _error = null;
        });
      case _PinChangeStep.confirmNew:
        if (pin != _newPin) {
          setState(() {
            _error = 'PIN kodlar mos kelmadi.';
            _step = _PinChangeStep.enterNew;
            _newPin = null;
          });
          return;
        }
        setState(() => _isLoading = true);
        final ok = await ref
            .read(authProvider.notifier)
            .changePin(_oldPin!, _newPin!);
        if (mounted) {
          if (ok) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('PIN kod muvaffaqiyatli o\'zgartirildi'),
                backgroundColor: AppColors.pos,
              ),
            );
            context.pop();
          } else {
            setState(() {
              _error =
                  'PIN kodni o\'zgartirishda xatolik. Eski PIN ni tekshiring.';
              _step = _PinChangeStep.enterOld;
              _oldPin = null;
              _newPin = null;
              _isLoading = false;
            });
          }
        }
    }
  }

  String get _title => switch (_step) {
    _PinChangeStep.enterOld => 'Joriy PIN ni kiriting',
    _PinChangeStep.enterNew => 'Yangi PIN kiriting',
    _PinChangeStep.confirmNew => 'Yangi PIN ni tasdiqlang',
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: VelmoraAppBar(subtitle: 'PIN o\'zgartirish'),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.s6),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(_title, style: AppText.title, textAlign: TextAlign.center),
                if (_isLoading)
                  const Padding(
                    padding: EdgeInsets.all(AppSpacing.s8),
                    child: SizedBox(
                      width: 42,
                      height: 42,
                      child: CircularProgressIndicator(strokeWidth: 3.5),
                    ),
                  )
                else
                  PinInputWidget(
                    key: ValueKey(_step),
                    onCompleted: _onPinEntered,
                    errorText: _error,
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

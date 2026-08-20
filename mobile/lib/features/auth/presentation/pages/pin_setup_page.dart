import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/mobirex_logo.dart';
import '../../../../shared/widgets/pin_input_widget.dart';
import '../providers/auth_provider.dart';

class PinSetupPage extends ConsumerStatefulWidget {
  const PinSetupPage({super.key});

  @override
  ConsumerState<PinSetupPage> createState() => _PinSetupPageState();
}

class _PinSetupPageState extends ConsumerState<PinSetupPage> {
  String? _firstPin;
  String? _error;
  bool _isConfirming = false;
  bool _isLoading = false;

  Future<void> _onPinEntered(String pin) async {
    if (!_isConfirming) {
      setState(() {
        _firstPin = pin;
        _isConfirming = true;
        _error = null;
      });
      return;
    }

    if (pin != _firstPin) {
      setState(() {
        _error = 'PIN kodlar mos kelmadi. Qaytadan boshlang.';
        _isConfirming = false;
        _firstPin = null;
      });
      return;
    }

    setState(() => _isLoading = true);
    final ok = await ref.read(authProvider.notifier).setPin(pin);
    if (mounted) {
      if (ok) {
        context.go('/phones/unsold');
      } else {
        setState(() {
          _error = 'PIN o\'rnatishda xatolik yuz berdi.';
          _isConfirming = false;
          _firstPin = null;
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.s6),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const MobirexLogo(size: 64),
                const SizedBox(height: 22),
                const Text(
                  'PIN o\'rnatish',
                  style: AppText.title,
                  textAlign: TextAlign.center,
                ),
                Padding(
                  padding: const EdgeInsets.only(top: AppSpacing.s2),
                  child: Text(
                    _isConfirming
                        ? 'PIN kodingizni tasdiqlang'
                        : '4 xonali PIN kod tanlang',
                    style: const TextStyle(
                      color: AppColors.ink2,
                      fontSize: 13,
                      height: 1.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
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
                    key: ValueKey(_isConfirming),
                    onCompleted: _onPinEntered,
                    errorText: _error,
                  ),
                Padding(
                  padding: const EdgeInsets.only(top: 22),
                  child: TextButton(
                    onPressed: () => context.go('/phones/unsold'),
                    child: const Text(
                      'Hozircha o\'tkazib yuborish',
                      style: TextStyle(
                        color: AppColors.action,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/mobirex_logo.dart';
import '../../../../shared/widgets/pin_input_widget.dart';
import '../providers/auth_provider.dart';

class PinVerifyPage extends ConsumerStatefulWidget {
  const PinVerifyPage({super.key});

  @override
  ConsumerState<PinVerifyPage> createState() => _PinVerifyPageState();
}

class _PinVerifyPageState extends ConsumerState<PinVerifyPage> {
  String? _error;
  bool _isLoading = false;

  Future<void> _verify(String pin) async {
    if (_isLoading) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });

    final ok = await ref.read(authProvider.notifier).verifyPin(pin);
    if (mounted) {
      if (!ok) {
        setState(() {
          _error = 'Noto\'g\'ri PIN. Qayta urinib ko\'ring.';
          _isLoading = false;
        });
      } else {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(authProvider).user;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.s6),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const MobirexLogo(size: 64),
                const Padding(
                  padding: EdgeInsets.only(top: 22),
                  child: Icon(
                    Icons.lock_outline,
                    size: 44,
                    color: AppColors.ink3,
                  ),
                ),
                const SizedBox(height: 14),
                const Text(
                  'PIN kodingizni kiriting',
                  style: AppText.title,
                  textAlign: TextAlign.center,
                ),
                if (user != null)
                  Padding(
                    padding: const EdgeInsets.only(top: AppSpacing.s2),
                    child: Text(
                      user.fullName.isNotEmpty ? user.fullName : user.username,
                      style: const TextStyle(
                        color: AppColors.ink2,
                        fontSize: 13,
                        height: 1.5,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                PinInputWidget(onCompleted: _verify, errorText: _error),
                Padding(
                  padding: const EdgeInsets.only(top: 22),
                  child: TextButton(
                    onPressed: () => ref.read(authProvider.notifier).logout(),
                    child: const Text(
                      'Boshqa hisob bilan kirish',
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

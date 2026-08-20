import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_links.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/mobirex_logo.dart';
import '../../../../shared/widgets/webview_page.dart';
import '../providers/auth_provider.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _obscurePassword = true;
  bool _isLoading = false;
  String? _error;
  bool _accountBlocked = false;

  // Kirish animatsiyasi — butun ilovadagi YAGONA kirish animatsiyasi
  // (`tokens.css`: logo 320ms ease-out, varaq 380ms + 80ms kechikish).
  late final AnimationController _entrance;
  late final Animation<double> _logoFade;
  late final Animation<Offset> _logoSlide;
  late final Animation<double> _sheetFade;
  late final Animation<Offset> _sheetSlide;

  @override
  void initState() {
    super.initState();
    _entrance = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 460),
    );

    // 0 → 320ms
    const logoCurve = Interval(0, 320 / 460, curve: AppCurves.press);
    _logoFade = CurvedAnimation(parent: _entrance, curve: logoCurve);
    _logoSlide = Tween<Offset>(
      begin: const Offset(0, -0.10),
      end: Offset.zero,
    ).animate(_logoFade);

    // 80ms → 460ms
    final sheetCurve = CurvedAnimation(
      parent: _entrance,
      curve: const Interval(80 / 460, 1, curve: AppCurves.enter),
    );
    _sheetFade = sheetCurve;
    _sheetSlide = Tween<Offset>(
      begin: const Offset(0, 0.05),
      end: Offset.zero,
    ).animate(sheetCurve);

    _entrance.forward();
  }

  @override
  void dispose() {
    _entrance.dispose();
    _usernameCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isLoading = true;
      _error = null;
      _accountBlocked = false;
    });
    try {
      await ref
          .read(authProvider.notifier)
          .login(_usernameCtrl.text.trim(), _passwordCtrl.text);
    } catch (e) {
      setState(() => _error = 'Tizimga kirishda xatolik yuz berdi.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(authProvider, (_, next) {
      if (next.status == AuthStatus.unauthenticated && next.error != null) {
        setState(() {
          _error = next.error;
          _accountBlocked = next.errorCode == 'account_blocked';
        });
      }
    });

    return Scaffold(
      backgroundColor: AppColors.bg,
      resizeToAvoidBottomInset: true,
      body: Column(
        children: [
          // Brend qismi — `.lg-brand`
          Expanded(
            child: SafeArea(
              bottom: false,
              child: FadeTransition(
                opacity: _logoFade,
                child: SlideTransition(
                  position: _logoSlide,
                  child: const Center(
                    child: MobirexLogo(
                      size: 88,
                      showText: true,
                      showTagline: true,
                    ),
                  ),
                ),
              ),
            ),
          ),
          // Ko'tarilgan varaq — `.lg-sheet`
          FadeTransition(
            opacity: _sheetFade,
            child: SlideTransition(
              position: _sheetSlide,
              child: Container(
                width: double.infinity,
                decoration: const BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: AppRadius.sheetRadius,
                  boxShadow: AppShadows.sheet,
                ),
                child: SafeArea(
                  top: false,
                  child: SingleChildScrollView(
                    padding: EdgeInsets.fromLTRB(
                      28,
                      AppSpacing.s4,
                      28,
                      MediaQuery.viewInsetsOf(context).bottom + 30,
                    ),
                    child: Center(
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 420),
                        child: Form(
                          key: _formKey,
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Center(
                                child: Container(
                                  width: 40,
                                  height: 4,
                                  margin: const EdgeInsets.only(bottom: 16),
                                  decoration: BoxDecoration(
                                    color: AppColors.lineStrong,
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                ),
                              ),
                              const Text(
                                'Tizimga kirish',
                                style: AppText.title,
                              ),
                              const SizedBox(height: AppSpacing.s4),
                              AppTextField(
                                label: 'Foydalanuvchi nomi',
                                controller: _usernameCtrl,
                                prefixIcon: Icons.person_outline,
                                textInputAction: TextInputAction.next,
                                validator: (v) => v == null || v.trim().isEmpty
                                    ? 'Majburiy'
                                    : null,
                              ),
                              const SizedBox(height: AppSpacing.s4),
                              AppTextField(
                                label: 'Parol',
                                controller: _passwordCtrl,
                                prefixIcon: Icons.lock_outline,
                                obscureText: _obscurePassword,
                                textInputAction: TextInputAction.done,
                                onFieldSubmitted: (_) => _login(),
                                validator: (v) => v == null || v.isEmpty
                                    ? 'Majburiy'
                                    : null,
                                suffixIcon: IconButton(
                                  tooltip: _obscurePassword
                                      ? 'Parolni ko\u2018rsatish'
                                      : 'Parolni yashirish',
                                  icon: Icon(
                                    _obscurePassword
                                        ? Icons.visibility_outlined
                                        : Icons.visibility_off_outlined,
                                    color: AppColors.ink3,
                                    size: 18,
                                  ),
                                  onPressed: () => setState(
                                    () => _obscurePassword = !_obscurePassword,
                                  ),
                                ),
                              ),
                              AnimatedSwitcher(
                                duration: const Duration(milliseconds: 180),
                                child: _error == null
                                    ? const SizedBox.shrink()
                                    : Padding(
                                        key: ValueKey('$_accountBlocked$_error'),
                                        padding: const EdgeInsets.only(
                                          top: 18,
                                        ),
                                        child: _accountBlocked
                                            ? _BlockedNotice(message: _error!)
                                            : InlineError(message: _error!),
                                      ),
                              ),
                              const SizedBox(height: AppSpacing.s6),
                              AppPrimaryButton(
                                label: 'Kirish',
                                block: true,
                                isLoading: _isLoading,
                                onPressed: _isLoading ? null : _login,
                              ),
                              const SizedBox(height: AppSpacing.s5),
                              const _ContactLink(),
                              const SizedBox(height: AppSpacing.s3),
                              _LegalLinks(
                                onOpen: (url, title) =>
                                    _openWebView(context, url, title),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _openWebView(BuildContext context, String url, String title) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => WebViewPage(url: url, title: title),
      ),
    );
  }

}

/// Login-time notice for a billing-blocked account. Distinct from the generic
/// wrong-credentials error: calm amber tone + a direct contact button.
class _BlockedNotice extends StatelessWidget {
  final String message;

  const _BlockedNotice({required this.message});

  Future<void> _contact(BuildContext context) async {
    final uri = Uri.parse(AppLinks.telegramSupportUrl);
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Telegram: ${AppLinks.telegramSupportUrl}'),
            backgroundColor: AppColors.neg,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        borderRadius: AppRadius.inputRadius,
        border: Border.all(color: AppColors.warn),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(
                Icons.pause_circle_outline,
                color: AppColors.warn,
                size: 18,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  message,
                  style: const TextStyle(
                    color: AppColors.ink,
                    fontSize: 13.5,
                    height: 1.45,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton.icon(
              onPressed: () => _contact(context),
              icon: const Icon(Icons.support_agent_outlined, size: 18),
              label: const Text('Yordam bilan bog‘lanish'),
              style: TextButton.styleFrom(
                foregroundColor: AppColors.warn,
                padding: const EdgeInsets.symmetric(horizontal: 8),
                minimumSize: const Size(0, 36),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                textStyle: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Ro'yxatdan o'tish yo'q — hisobi yo'q odam uchun yagona kirish nuqtasi.
///
/// Ko'rinadigan bo'lishi shart: tinch ajratgich, savol `--ink-2` da,
/// "Bog'lanish" esa `--action` (brend to'q sariq) 14px/w600 da. Kirish
/// tugmasi bilan raqobatlashmaydi, lekin ko'zdan qochmaydi ham.
class _ContactLink extends StatelessWidget {
  const _ContactLink();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Divider(color: AppColors.line, height: 1, thickness: 1),
        const SizedBox(height: AppSpacing.s2),
        InkWell(
          onTap: () => context.push('/contact'),
          borderRadius: AppRadius.chipRadius,
          child: Container(
            // 44px — Apple'ning minimal tegish maydoni.
            constraints: const BoxConstraints(minHeight: 44),
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.s2),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  'Hisobingiz yo‘qmi?',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: AppColors.ink2,
                  ),
                ),
                SizedBox(width: AppSpacing.s2),
                Text(
                  'Bog‘lanish',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppColors.action,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _LegalLinks extends StatelessWidget {
  final void Function(String url, String title) onOpen;

  const _LegalLinks({required this.onOpen});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.center,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 4,
      children: [
        TextButton(
          onPressed: () => onOpen(
            AppLinks.privacyPolicyUrl,
            'Maxfiylik siyosati',
          ),
          style: TextButton.styleFrom(
            foregroundColor: AppColors.ink3,
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: const Text(
            'Maxfiylik siyosati',
            style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w500),
          ),
        ),
        const Text(
          '·',
          style: TextStyle(color: AppColors.ink3, fontSize: 14),
        ),
        TextButton(
          onPressed: () => onOpen(AppLinks.termsUrl, 'Shartlar'),
          style: TextButton.styleFrom(
            foregroundColor: AppColors.ink3,
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: const Text(
            'Foydalanish shartlari',
            style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w500),
          ),
        ),
      ],
    );
  }
}

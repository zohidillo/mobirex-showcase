import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_select_sheet.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/mobirex_logo.dart';
import '../../data/models/contact_request.dart';
import '../providers/contact_request_provider.dart';

/// Telefon raqamini `90 123 45 67` ko'rinishida guruhlaydi (2-3-2-2).
/// Maydonda `+998` prefiks alohida ko'rsatiladi, shuning uchun bu yerda
/// faqat 9 ta raqam bo'ladi.
class _PhoneMaskFormatter extends TextInputFormatter {
  static const _groups = [2, 3, 2, 2];

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    final digits = newValue.text.replaceAll(RegExp(r'\D'), '');
    final trimmed = digits.length > 9 ? digits.substring(0, 9) : digits;

    final buffer = StringBuffer();
    var index = 0;
    for (final size in _groups) {
      if (index >= trimmed.length) break;
      if (buffer.isNotEmpty) buffer.write(' ');
      final end = (index + size).clamp(0, trimmed.length);
      buffer.write(trimmed.substring(index, end));
      index = end;
    }

    final text = buffer.toString();
    return TextEditingValue(
      text: text,
      selection: TextSelection.collapsed(offset: text.length),
    );
  }
}

class ContactRequestPage extends ConsumerStatefulWidget {
  const ContactRequestPage({super.key});

  @override
  ConsumerState<ContactRequestPage> createState() => _ContactRequestPageState();
}

class _ContactRequestPageState extends ConsumerState<ContactRequestPage>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _phoneCtrl = TextEditingController();
  final _regionCtrl = TextEditingController();
  RegionModel? _region;
  String? _regionError;

  // Login ekranidagi bilan bir xil kirish animatsiyasi — bir xil ilova
  // hissi qolishi uchun (logo tushadi, varaq ko'tariladi).
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

    const logoCurve = Interval(0, 320 / 460, curve: AppCurves.press);
    _logoFade = CurvedAnimation(parent: _entrance, curve: logoCurve);
    _logoSlide = Tween<Offset>(
      begin: const Offset(0, -0.10),
      end: Offset.zero,
    ).animate(_logoFade);

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
    _phoneCtrl.dispose();
    _regionCtrl.dispose();
    super.dispose();
  }

  void _backToLogin() {
    // Login'dan `push` bilan kelinadi, shuning uchun odatda `pop` yetadi;
    // to'g'ridan-to'g'ri havola bilan kirilgan holat uchun zaxira yo'l.
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/login');
    }
  }

  Future<void> _pickRegion(List<RegionModel> regions) async {
    FocusScope.of(context).unfocus();
    final selected = await showAppSelectSheet<String>(
      context: context,
      title: 'Viloyat',
      selected: _region?.value,
      options: regions
          .map((r) => AppSelectOption(value: r.value, label: r.label))
          .toList(),
    );
    if (selected == null || !mounted) return;
    setState(() {
      _region = regions.firstWhere((r) => r.value == selected);
      _regionCtrl.text = _region!.label;
      _regionError = null;
    });
  }

  Future<void> _submit() async {
    final formOk = _formKey.currentState!.validate();
    final regionOk = _region != null;
    if (!regionOk) setState(() => _regionError = 'Viloyatni tanlang');
    if (!formOk || !regionOk) return;

    FocusScope.of(context).unfocus();
    final digits = _phoneCtrl.text.replaceAll(RegExp(r'\D'), '');
    await ref
        .read(contactRequestProvider.notifier)
        .submit(phone: '+998$digits', region: _region!.value);
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(contactRequestProvider);

    return Scaffold(
      backgroundColor: AppColors.bg,
      resizeToAvoidBottomInset: true,
      body: Column(
        children: [
          Expanded(
            child: SafeArea(
              bottom: false,
              child: Stack(
                children: [
                  Align(
                    alignment: Alignment.topLeft,
                    child: FadeTransition(
                      opacity: _logoFade,
                      child: IconButton(
                        tooltip: 'Orqaga',
                        onPressed: _backToLogin,
                        icon: const Icon(
                          Icons.arrow_back,
                          color: AppColors.ink2,
                        ),
                      ),
                    ),
                  ),
                  FadeTransition(
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
                ],
              ),
            ),
          ),
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
                        child: AnimatedSwitcher(
                          duration: const Duration(milliseconds: 220),
                          child: state.isSuccess
                              ? _SuccessView(onBack: _backToLogin)
                              : _buildForm(state),
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

  Widget _buildForm(ContactRequestState state) {
    final regionsAsync = ref.watch(regionsProvider);

    return Form(
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
          const Text('Bog‘lanish', style: AppText.title),
          const SizedBox(height: AppSpacing.s2),
          const Text(
            'Telefon raqamingizni qoldiring — mutaxassislarimiz siz bilan '
            'bog‘lanib, Mobirex haqida batafsil aytib beradi.',
            style: TextStyle(
              fontSize: 13,
              height: 1.45,
              color: AppColors.ink2,
            ),
          ),
          const SizedBox(height: AppSpacing.s5),
          AppTextField(
            label: 'Telefon raqami',
            controller: _phoneCtrl,
            prefixIcon: Icons.phone_outlined,
            prefixText: '+998 ',
            hint: '90 123 45 67',
            keyboardType: TextInputType.phone,
            textInputAction: TextInputAction.done,
            inputFormatters: [_PhoneMaskFormatter()],
            enabled: !state.isSubmitting,
            validator: (v) {
              final digits = (v ?? '').replaceAll(RegExp(r'\D'), '');
              if (digits.isEmpty) return 'Majburiy';
              if (digits.length < 9) return 'Raqam to‘liq emas';
              return null;
            },
          ),
          const SizedBox(height: AppSpacing.s4),
          regionsAsync.when(
            data: (regions) => _RegionField(
              controller: _regionCtrl,
              error: _regionError,
              enabled: !state.isSubmitting,
              onTap: () => _pickRegion(regions),
            ),
            loading: () => const _RegionPlaceholder(
              text: 'Viloyatlar yuklanmoqda…',
            ),
            error: (_, _) => _RegionPlaceholder(
              text: 'Viloyatlarni yuklab bo‘lmadi',
              isError: true,
              onRetry: () => ref.invalidate(regionsProvider),
            ),
          ),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 180),
            child: state.error == null
                ? const SizedBox.shrink()
                : Padding(
                    key: ValueKey(state.error),
                    padding: const EdgeInsets.only(top: 18),
                    child: InlineError(message: state.error!),
                  ),
          ),
          const SizedBox(height: AppSpacing.s6),
          AppPrimaryButton(
            label: 'Yuborish',
            block: true,
            isLoading: state.isSubmitting,
            onPressed: state.isSubmitting ? null : _submit,
          ),
          const SizedBox(height: AppSpacing.s4),
        ],
      ),
    );
  }
}

/// Viloyat maydoni — bosilganda `AppSelectSheet` ochiladi.
class _RegionField extends StatelessWidget {
  const _RegionField({
    required this.controller,
    required this.error,
    required this.enabled,
    required this.onTap,
  });

  final TextEditingController controller;
  final String? error;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return AppTextField(
      label: 'Viloyat',
      hint: 'Tanlang',
      readOnly: true,
      enabled: enabled,
      onTap: enabled ? onTap : null,
      controller: controller,
      prefixIcon: Icons.location_on_outlined,
      suffixIcon: const Icon(
        Icons.keyboard_arrow_down,
        color: AppColors.ink3,
        size: 20,
      ),
      validator: (_) => error,
      autovalidateMode: AutovalidateMode.always,
    );
  }
}

/// Viloyatlar hali kelmagan yoki kelmay qolgan holat — forma hech qachon
/// bo'sh va ishlatib bo'lmaydigan ko'rinishda qolmaydi.
class _RegionPlaceholder extends StatelessWidget {
  const _RegionPlaceholder({
    required this.text,
    this.isError = false,
    this.onRetry,
  });

  final String text;
  final bool isError;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s4,
        vertical: 14,
      ),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: AppRadius.inputRadius,
        border: Border.all(
          color: isError ? AppColors.neg : Colors.transparent,
          width: 1.5,
        ),
      ),
      child: Row(
        children: [
          Icon(
            isError ? Icons.error_outline : Icons.location_on_outlined,
            size: 18,
            color: isError ? AppColors.neg : AppColors.ink3,
          ),
          const SizedBox(width: AppSpacing.s3),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: AppColors.ink2,
              ),
            ),
          ),
          if (onRetry != null)
            TextButton(
              onPressed: onRetry,
              style: TextButton.styleFrom(
                foregroundColor: AppColors.action,
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.s2),
                minimumSize: const Size(0, 36),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                textStyle: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
              child: const Text('Qayta urinish'),
            ),
        ],
      ),
    );
  }
}

/// Yuborilgandan keyingi tinch tasdiq — forma o'rnini egallaydi.
class _SuccessView extends StatelessWidget {
  const _SuccessView({required this.onBack});

  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Center(
          child: Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.only(bottom: AppSpacing.s6),
            decoration: BoxDecoration(
              color: AppColors.lineStrong,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ),
        const Center(
          child: Icon(
            Icons.check_circle_outline,
            size: 44,
            color: AppColors.action,
          ),
        ),
        const SizedBox(height: AppSpacing.s4),
        const Text(
          'So‘rovingiz qabul qilindi',
          textAlign: TextAlign.center,
          style: AppText.title,
        ),
        const SizedBox(height: AppSpacing.s2),
        const Text(
          'Mutaxassislarimiz tez orada siz bilan bog‘lanishadi.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 14,
            height: 1.5,
            color: AppColors.ink2,
          ),
        ),
        const SizedBox(height: AppSpacing.s7),
        AppPrimaryButton(
          label: 'Kirish sahifasiga qaytish',
          block: true,
          onPressed: onBack,
        ),
        const SizedBox(height: AppSpacing.s4),
      ],
    );
  }
}

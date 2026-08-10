import 'package:flutter/material.dart';

/// Mobirex dizayn tizimi — manba: `new_design_app/redesign3/tokens.css`.
///
/// Palitra QULFLANGAN: bg #001524 · action #DF6C00 · ink #F0EFF4.
/// Shkala #001524 dan bir xil hue (~205°) bo'ylab yorqinlashtirib chiqarilgan.
///
/// CSS `font-weight` → Flutter `FontWeight` moslashuvi (Flutter faqat 100
/// qadamli vaznlarni biladi):
///   850/800 → w800 · 750/700 → w700 · 650/600 → w600 · 500 → w500
///
/// CSS `letter-spacing` em → Flutter px: `ls_px = em × fontSize`.

// ---------------------------------------------------------------------------
// PALITRA
// ---------------------------------------------------------------------------

/// Butun tizimning rang to'plami.
///
/// `ThemeExtension` bo'lgani uchun kelajakda ikkinchi palitra qo'shish =
/// bitta yangi `static const AppPalette(...)` yozib, uni
/// [AppTheme.build] ga berish. Boshqa hech narsa o'zgarmaydi.
/// Widgetlar ichida: `Theme.of(context).extension<AppPalette>()!`.
///
/// Diqqat: `const` konstruktorlar (ro'yxatdagi kartalar uchun majburiy)
/// `context` dan rang o'qiy olmaydi — shuning uchun kundalik ish uchun
/// [AppColors] statik konstantalari ishlatiladi. Ular hozirgi
/// [AppPalette.inkBlack] bilan bir xil qiymatga ega.
@immutable
class AppPalette extends ThemeExtension<AppPalette> {
  const AppPalette({
    required this.bg,
    required this.surface,
    required this.card,
    required this.cardPressed,
    required this.line,
    required this.lineStrong,
    required this.ink,
    required this.ink2,
    required this.ink3,
    required this.action,
    required this.actionPressed,
    required this.onAction,
    required this.edgeNeutral,
    required this.pos,
    required this.neg,
    required this.warn,
  });

  /// Asosiy fon — qulflangan.
  final Color bg;

  /// App bar, drawer, bottom sheet: bg+1.
  final Color surface;

  /// Kartalar, inputlar: surface+1.
  final Color card;

  /// Bosilgan karta: card+1.
  final Color cardPressed;

  /// Hairline — card ustida sezilarli.
  final Color line;

  /// Input osti, urg'u chegarasi.
  final Color lineStrong;

  /// Asosiy matn — qulflangan.
  final Color ink;

  /// Ikkilamchi matn.
  final Color ink2;

  /// Uchlamchi / meta matn.
  final Color ink3;

  /// Asosiy harakat — qulflangan.
  final Color action;

  /// Bosilgan harakat.
  final Color actionPressed;

  /// Orange ustidagi matn (to'q — AA o'tadi).
  final Color onAction;

  /// Kartaning odatiy chap qirrasi.
  final Color edgeNeutral;

  /// Musbat pul.
  final Color pos;

  /// Manfiy pul.
  final Color neg;

  /// Grace banner amber.
  final Color warn;

  /// Qulflangan "Ink Black" palitrasi — `tokens.css` `:root` bloki.
  static const AppPalette inkBlack = AppPalette(
    bg: Color(0xFF001524),
    surface: Color(0xFF07222F),
    card: Color(0xFF0E2C3D),
    cardPressed: Color(0xFF17394C),
    line: Color(0xFF1B3E52),
    lineStrong: Color(0xFF2E5670),
    ink: Color(0xFFF0EFF4),
    ink2: Color(0xFF9DB2C1),
    ink3: Color(0xFF61798B),
    action: Color(0xFFDF6C00),
    actionPressed: Color(0xFFC25E00),
    onAction: Color(0xFF001524),
    edgeNeutral: Color(0xFF2E4C60),
    pos: Color(0xFF4EC072),
    neg: Color(0xFFF0655C),
    warn: Color(0xFFE8A33D),
  );

  @override
  AppPalette copyWith({
    Color? bg,
    Color? surface,
    Color? card,
    Color? cardPressed,
    Color? line,
    Color? lineStrong,
    Color? ink,
    Color? ink2,
    Color? ink3,
    Color? action,
    Color? actionPressed,
    Color? onAction,
    Color? edgeNeutral,
    Color? pos,
    Color? neg,
    Color? warn,
  }) {
    return AppPalette(
      bg: bg ?? this.bg,
      surface: surface ?? this.surface,
      card: card ?? this.card,
      cardPressed: cardPressed ?? this.cardPressed,
      line: line ?? this.line,
      lineStrong: lineStrong ?? this.lineStrong,
      ink: ink ?? this.ink,
      ink2: ink2 ?? this.ink2,
      ink3: ink3 ?? this.ink3,
      action: action ?? this.action,
      actionPressed: actionPressed ?? this.actionPressed,
      onAction: onAction ?? this.onAction,
      edgeNeutral: edgeNeutral ?? this.edgeNeutral,
      pos: pos ?? this.pos,
      neg: neg ?? this.neg,
      warn: warn ?? this.warn,
    );
  }

  @override
  AppPalette lerp(ThemeExtension<AppPalette>? other, double t) {
    if (other is! AppPalette) return this;
    return AppPalette(
      bg: Color.lerp(bg, other.bg, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      card: Color.lerp(card, other.card, t)!,
      cardPressed: Color.lerp(cardPressed, other.cardPressed, t)!,
      line: Color.lerp(line, other.line, t)!,
      lineStrong: Color.lerp(lineStrong, other.lineStrong, t)!,
      ink: Color.lerp(ink, other.ink, t)!,
      ink2: Color.lerp(ink2, other.ink2, t)!,
      ink3: Color.lerp(ink3, other.ink3, t)!,
      action: Color.lerp(action, other.action, t)!,
      actionPressed: Color.lerp(actionPressed, other.actionPressed, t)!,
      onAction: Color.lerp(onAction, other.onAction, t)!,
      edgeNeutral: Color.lerp(edgeNeutral, other.edgeNeutral, t)!,
      pos: Color.lerp(pos, other.pos, t)!,
      neg: Color.lerp(neg, other.neg, t)!,
      warn: Color.lerp(warn, other.warn, t)!,
    );
  }
}

/// Kundalik ish uchun rang tokenlari — `const` kontekstlarda ishlaydi.
class AppColors {
  const AppColors._();

  // --- tokens.css RANG bloki -----------------------------------------------

  /// `--bg` #001524
  static const Color bg = Color(0xFF001524);

  /// `--surface` #07222F
  static const Color surface = Color(0xFF07222F);

  /// `--card` #0E2C3D
  static const Color card = Color(0xFF0E2C3D);

  /// `--card-pressed` #17394C
  static const Color cardPressed = Color(0xFF17394C);

  /// `--line` #1B3E52
  static const Color line = Color(0xFF1B3E52);

  /// `--line-strong` #2E5670
  static const Color lineStrong = Color(0xFF2E5670);

  /// `--ink` #F0EFF4
  static const Color ink = Color(0xFFF0EFF4);

  /// `--ink-2` #9DB2C1
  static const Color ink2 = Color(0xFF9DB2C1);

  /// `--ink-3` #61798B
  static const Color ink3 = Color(0xFF61798B);

  /// `--action` #DF6C00
  static const Color action = Color(0xFFDF6C00);

  /// `--action-pressed` #C25E00
  static const Color actionPressed = Color(0xFFC25E00);

  /// `--on-action` #001524
  static const Color onAction = Color(0xFF001524);

  /// `--edge-neutral` #2E4C60
  static const Color edgeNeutral = Color(0xFF2E4C60);

  /// `--pos` #4EC072
  static const Color pos = Color(0xFF4EC072);

  /// `--neg` #F0655C
  static const Color neg = Color(0xFFF0655C);

  /// `--warn` #E8A33D
  static const Color warn = Color(0xFFE8A33D);

  /// Modal orqa foni (scrim) — barcha dialog/sheet uchun BITTA manba.
  static const Color scrim = Color(0x8C000509);

  /// Bosilgan tugma ustidagi qatlam.
  static const Color overlayPressed = Color(0x4D001524);
}

// ---------------------------------------------------------------------------
// SHRIFT SHKALASI
// ---------------------------------------------------------------------------

/// `tokens.css` SHRIFT SHKALASI bloki.
class AppText {
  const AppText._();

  /// Pul raqamlari ro'yxatda tik turishi uchun.
  static const List<FontFeature> _tabular = [FontFeature.tabularFigures()];

  /// `--fs-display` 28/800, ls -0.02em, tabular — hero narx.
  static const TextStyle display = TextStyle(
    fontSize: 28,
    fontWeight: FontWeight.w800,
    letterSpacing: -0.56,
    height: 1.15,
    color: AppColors.ink,
    fontFeatures: _tabular,
  );

  /// `--fs-title` 20/750, ls -0.02em — ekran va sheet sarlavhasi.
  static const TextStyle title = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.4,
    height: 1.15,
    color: AppColors.ink,
  );

  /// `--fs-body-lg` 16/650, ls -0.01em — model / ism.
  static const TextStyle bodyLg = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.16,
    color: AppColors.ink,
  );

  /// `--fs-body` 14/500 — oddiy matn, input.
  static const TextStyle body = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w500,
    color: AppColors.ink,
  );

  /// `--fs-label` 12/600 — tugma yorlig'i, yordamchi matn.
  static const TextStyle label = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w600,
    color: AppColors.ink,
  );

  /// `--fs-meta` 10.5/600, UPPERCASE, ls +0.08em — meta qator.
  ///
  /// Matnni o'zingiz `.toUpperCase()` qilasiz — Flutter'da CSS
  /// `text-transform` ekvivalenti yo'q.
  static const TextStyle meta = TextStyle(
    fontSize: 10.5,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.84,
    color: AppColors.ink3,
  );

  /// `--fs-micro` 9.5/700, UPPERCASE, ls +0.14em — eng kichik yozuv.
  static const TextStyle micro = TextStyle(
    fontSize: 9.5,
    fontWeight: FontWeight.w700,
    letterSpacing: 1.33,
    color: AppColors.ink3,
  );

  // --- komponentga xos o'lchamlar (CSS'dan, shkala tashqarisida) ------------

  /// `.sect-h` 11/800, UPPERCASE, ls +0.14em — bo'lim sarlavhasi.
  static const TextStyle sectionLabel = TextStyle(
    fontSize: 11,
    fontWeight: FontWeight.w800,
    letterSpacing: 1.54,
    color: AppColors.ink3,
  );

  /// `.mb .val` 24/800, tabular — dashboard metrika qiymati.
  static const TextStyle metricValue = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w800,
    letterSpacing: -0.48,
    color: AppColors.ink,
    fontFeatures: _tabular,
  );

  /// `.totalbar .tv` 22/800, tabular — jami banner qiymati.
  static const TextStyle totalValue = TextStyle(
    fontSize: 22,
    fontWeight: FontWeight.w800,
    letterSpacing: -0.44,
    color: AppColors.ink,
    fontFeatures: _tabular,
  );

  /// `.inp` 15/500 — input ichidagi matn.
  static const TextStyle input = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w500,
    color: AppColors.ink,
  );
}

// ---------------------------------------------------------------------------
// BO'SHLIQ / RADIUS / SOYA / O'TISH
// ---------------------------------------------------------------------------

/// `tokens.css` BO'SHLIQ bloki — 4px asos.
class AppSpacing {
  const AppSpacing._();

  static const double s1 = 4;
  static const double s2 = 8;
  static const double s3 = 12;
  static const double s4 = 16;
  static const double s5 = 20;
  static const double s6 = 24;
  static const double s7 = 28;
  static const double s8 = 32;
}

/// `tokens.css` RADIUS bloki.
class AppRadius {
  const AppRadius._();

  /// `--r-card` 12
  static const double card = 12;

  /// `--r-input` 10
  static const double input = 10;

  /// `--r-chip` 8
  static const double chip = 8;

  /// `--r-sheet` 22
  static const double sheet = 22;

  /// Header blokining pastki burchagi, FAB va dialog.
  static const double block = 16;

  static const BorderRadius cardRadius = BorderRadius.all(
    Radius.circular(card),
  );
  static const BorderRadius inputRadius = BorderRadius.all(
    Radius.circular(input),
  );
  static const BorderRadius chipRadius = BorderRadius.all(
    Radius.circular(chip),
  );
  static const BorderRadius blockRadius = BorderRadius.all(
    Radius.circular(block),
  );

  /// Bottom sheet — faqat yuqori burchaklar.
  static const BorderRadius sheetRadius = BorderRadius.vertical(
    top: Radius.circular(sheet),
  );
}

/// `tokens.css` SOYA bloki — faqat ikkitasi (+ bosilgan holat).
///
/// Qoida: bitta qatlam, blur ≤ 12, y ≤ 4, opacity ≤ 0.35, `spreadRadius` YO'Q.
class AppShadows {
  const AppShadows._();

  /// `--shadow-card` `0 3px 10px rgba(0,0,0,.32)`
  static const List<BoxShadow> card = [
    BoxShadow(color: Color(0x52000000), blurRadius: 10, offset: Offset(0, 3)),
  ];

  /// `.card.is-pressed` `0 1px 4px rgba(0,0,0,.28)`
  static const List<BoxShadow> cardPressed = [
    BoxShadow(color: Color(0x47000000), blurRadius: 4, offset: Offset(0, 1)),
  ];

  /// `--shadow-sheet` `0 -4px 12px rgba(0,0,0,.45)` — faqat sheet va dialog.
  static const List<BoxShadow> sheet = [
    BoxShadow(color: Color(0x73000000), blurRadius: 12, offset: Offset(0, -4)),
  ];
}

/// `tokens.css` O'TISH bloki.
class AppDurations {
  const AppDurations._();

  /// `--t-press` 120ms — bosish javobi.
  static const Duration press = Duration(milliseconds: 120);

  /// `--t-enter` 380ms — kirish animatsiyasi (FAQAT login varag'i).
  static const Duration enter = Duration(milliseconds: 380);

  /// Login logotipi 320ms.
  static const Duration enterLogo = Duration(milliseconds: 320);

  /// Login varag'ining kechikishi.
  static const Duration enterDelay = Duration(milliseconds: 80);
}

/// [AppDurations] bilan juft keladigan egri chiziqlar.
class AppCurves {
  const AppCurves._();

  /// `ease-out`
  static const Curve press = Curves.easeOut;

  /// `cubic-bezier(0.16, 1, 0.3, 1)`
  static const Curve enter = Cubic(0.16, 1.0, 0.3, 1.0);
}

// ---------------------------------------------------------------------------
// THEMEDATA
// ---------------------------------------------------------------------------

class AppTheme {
  const AppTheme._();

  /// Berilgan palitradan to'liq [ThemeData] quradi.
  ///
  /// Kelajakda ikkinchi tema = `AppTheme.build(AppPalette.<yangi>)`.
  static ThemeData build(AppPalette p) {
    final colorScheme = ColorScheme.dark(
      primary: p.action,
      onPrimary: p.onAction,
      secondary: p.action,
      onSecondary: p.onAction,
      surface: p.surface,
      onSurface: p.ink,
      surfaceContainerHighest: p.card,
      error: p.neg,
      onError: p.onAction,
      outline: p.lineStrong,
      outlineVariant: p.line,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: p.bg,
      canvasColor: p.bg,
      splashFactory: InkRipple.splashFactory,
      extensions: <ThemeExtension<dynamic>>[p],

      textTheme: _textTheme(p),
      iconTheme: IconThemeData(color: p.ink2, size: 22),
      primaryIconTheme: IconThemeData(color: p.ink2, size: 22),

      appBarTheme: AppBarTheme(
        backgroundColor: p.surface,
        foregroundColor: p.ink,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: AppText.title.copyWith(color: p.ink),
        iconTheme: IconThemeData(color: p.ink2, size: 22),
        actionsIconTheme: IconThemeData(color: p.ink2, size: 22),
      ),

      drawerTheme: DrawerThemeData(
        backgroundColor: p.surface,
        surfaceTintColor: Colors.transparent,
        // `.dimmed` rgba(0,5,9,.55)
        scrimColor: const Color(0x8C000509),
        elevation: 0,
      ),

      cardTheme: CardThemeData(
        color: p.card,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.cardRadius,
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: p.card,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 15,
          vertical: 15,
        ),
        border: const OutlineInputBorder(
          borderRadius: AppRadius.inputRadius,
          borderSide: BorderSide(color: Colors.transparent, width: 1.5),
        ),
        enabledBorder: const OutlineInputBorder(
          borderRadius: AppRadius.inputRadius,
          borderSide: BorderSide(color: Colors.transparent, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: AppRadius.inputRadius,
          borderSide: BorderSide(color: p.action, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: AppRadius.inputRadius,
          borderSide: BorderSide(color: p.neg, width: 1.5),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: AppRadius.inputRadius,
          borderSide: BorderSide(color: p.neg, width: 1.5),
        ),
        disabledBorder: const OutlineInputBorder(
          borderRadius: AppRadius.inputRadius,
          borderSide: BorderSide(color: Colors.transparent, width: 1.5),
        ),
        hintStyle: AppText.input.copyWith(color: p.ink3),
        labelStyle: AppText.meta.copyWith(color: p.ink3, letterSpacing: 1.26),
        floatingLabelStyle: AppText.meta.copyWith(
          color: p.ink3,
          letterSpacing: 1.26,
        ),
        errorStyle: TextStyle(fontSize: 12, color: p.neg),
        prefixStyle: AppText.input,
        suffixStyle: AppText.input,
        prefixIconColor: p.ink3,
        suffixIconColor: p.ink3,
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: p.action,
          foregroundColor: p.onAction,
          disabledBackgroundColor: p.action.withValues(alpha: 0.45),
          disabledForegroundColor: p.onAction.withValues(alpha: 0.7),
          minimumSize: const Size(double.infinity, 54),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.s5),
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.inputRadius,
          ),
          elevation: 0,
          animationDuration: AppDurations.press,
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: p.action,
          textStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.inputRadius,
          ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: p.ink,
          side: BorderSide(color: p.lineStrong),
          minimumSize: const Size(0, 40),
          textStyle: const TextStyle(
            fontSize: 12.5,
            fontWeight: FontWeight.w600,
          ),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.inputRadius,
          ),
        ),
      ),

      // `.fab` — 58×58, 16px radius.
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: p.action,
        foregroundColor: p.onAction,
        sizeConstraints: const BoxConstraints.tightFor(width: 58, height: 58),
        iconSize: 24,
        elevation: 3,
        focusElevation: 3,
        hoverElevation: 3,
        highlightElevation: 1,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.blockRadius,
        ),
      ),

      dialogTheme: DialogThemeData(
        backgroundColor: p.surface,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.blockRadius,
        ),
        titleTextStyle: const TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: AppColors.ink,
        ),
        contentTextStyle: TextStyle(fontSize: 14, height: 1.5, color: p.ink2),
      ),

      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: p.surface,
        surfaceTintColor: Colors.transparent,
        modalBackgroundColor: p.surface,
        elevation: 0,
        modalElevation: 0,
        showDragHandle: false,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.sheetRadius,
        ),
      ),

      snackBarTheme: SnackBarThemeData(
        backgroundColor: p.cardPressed,
        contentTextStyle: TextStyle(
          fontSize: 13.5,
          fontWeight: FontWeight.w600,
          color: p.ink,
        ),
        actionTextColor: p.action,
        behavior: SnackBarBehavior.floating,
        elevation: 0,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.inputRadius,
        ),
      ),

      dividerTheme: DividerThemeData(color: p.line, thickness: 1, space: 1),

      chipTheme: ChipThemeData(
        backgroundColor: p.card,
        selectedColor: p.card,
        disabledColor: p.card,
        labelStyle: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: p.ink,
        ),
        side: BorderSide(color: p.lineStrong),
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.chipRadius,
        ),
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.s3),
      ),

      listTileTheme: ListTileThemeData(
        iconColor: p.ink3,
        textColor: p.ink,
        titleTextStyle: AppText.body.copyWith(fontSize: 15, color: p.ink),
        subtitleTextStyle: AppText.label.copyWith(color: p.ink3),
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.inputRadius,
        ),
      ),

      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: p.action,
        circularTrackColor: p.cardPressed,
        linearTrackColor: p.cardPressed,
      ),

      tabBarTheme: TabBarThemeData(
        labelColor: p.action,
        unselectedLabelColor: p.ink3,
        indicatorColor: p.action,
        dividerColor: p.line,
        labelStyle: AppText.label.copyWith(fontWeight: FontWeight.w700),
        unselectedLabelStyle: AppText.label,
      ),

      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected) ? p.onAction : p.ink3,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected) ? p.action : p.card,
        ),
        trackOutlineColor: WidgetStatePropertyAll(p.lineStrong),
      ),

      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected)
              ? p.action
              : Colors.transparent,
        ),
        checkColor: WidgetStatePropertyAll(p.onAction),
        side: BorderSide(color: p.lineStrong, width: 1.5),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.s1),
        ),
      ),

      radioTheme: RadioThemeData(
        fillColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected) ? p.action : p.lineStrong,
        ),
      ),

      popupMenuTheme: PopupMenuThemeData(
        color: p.surface,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        textStyle: AppText.body.copyWith(fontSize: 15),
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.inputRadius,
        ),
      ),

      textSelectionTheme: TextSelectionThemeData(
        cursorColor: p.action,
        selectionColor: p.action.withValues(alpha: 0.3),
        selectionHandleColor: p.action,
      ),

      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: p.surface,
        selectedItemColor: p.action,
        unselectedItemColor: p.ink3,
        elevation: 0,
        type: BottomNavigationBarType.fixed,
      ),
    );
  }

  static TextTheme _textTheme(AppPalette p) {
    return TextTheme(
      displayLarge: AppText.display.copyWith(color: p.ink),
      displayMedium: AppText.display.copyWith(color: p.ink),
      displaySmall: AppText.display.copyWith(color: p.ink),
      headlineLarge: AppText.title.copyWith(color: p.ink),
      headlineMedium: AppText.title.copyWith(color: p.ink),
      headlineSmall: AppText.title.copyWith(color: p.ink),
      titleLarge: AppText.title.copyWith(color: p.ink),
      titleMedium: AppText.bodyLg.copyWith(color: p.ink),
      titleSmall: AppText.body.copyWith(fontWeight: FontWeight.w600),
      bodyLarge: AppText.bodyLg.copyWith(color: p.ink),
      bodyMedium: AppText.body.copyWith(color: p.ink),
      bodySmall: AppText.label.copyWith(color: p.ink2),
      labelLarge: AppText.label.copyWith(color: p.ink),
      labelMedium: AppText.meta.copyWith(color: p.ink3),
      labelSmall: AppText.micro.copyWith(color: p.ink3),
    );
  }

  /// Yagona faol tema — qulflangan "Ink Black" palitrasi.
  static ThemeData get dark => build(AppPalette.inkBlack);

  /// Yorug' tema hozircha YO'Q — dizayn tizimi faqat qorong'i
  /// (`tokens.css` da yorug' palitra mavjud emas).
  ///
  /// Getter saqlanadi, chunki uni import qilgan joylar sinmasligi kerak.
  @Deprecated('Yorug\' tema yo\'q — AppTheme.dark ishlating')
  static ThemeData get light => dark;
}

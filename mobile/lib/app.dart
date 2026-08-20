import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
// Tema almashtirish vaqtincha uzilgan — pastdagi izohga qarang.
// import 'core/theme/theme_provider.dart';

/// Root messenger so SnackBars can survive route changes (e.g. showing a
/// confirmation after the user is navigated back to login).
final rootScaffoldMessengerKey = GlobalKey<ScaffoldMessengerState>();

class VelmoraApp extends ConsumerWidget {
  const VelmoraApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    // Redizayn: dizayn tizimi hozircha FAQAT qorong'i (tokens.css da yorug'
    // palitra yo'q), shuning uchun tema almashtirish vaqtincha uzib qo'yildi.
    // Logika saqlanib qoldi — `themeModeProvider` va `theme_provider.dart`
    // tegilmagan, server hali ham temani yuboradi va saqlaydi.
    //
    // Kelajakda ikkinchi palitra qo'shilganda: `AppPalette` ning yangi
    // `static const` nusxasini yozib, quyidagi uch qatorni qaytaring.
    //
    // final themeMode = ref.watch(themeModeProvider);

    return MaterialApp.router(
      title: 'Mobirex',
      debugShowCheckedModeBanner: false,
      scaffoldMessengerKey: rootScaffoldMessengerKey,
      theme: AppTheme.dark,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.dark,
      // theme: AppTheme.light,
      // darkTheme: AppTheme.dark,
      // themeMode: themeMode,
      routerConfig: router,
    );
  }
}

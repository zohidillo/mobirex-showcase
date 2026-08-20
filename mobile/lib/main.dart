import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';
import 'core/error_reporting/error_reporter.dart';
import 'core/error_reporting/flutter_handler.dart';

void main() {
  runZonedGuarded(() async {
    WidgetsFlutterBinding.ensureInitialized();
    await ErrorReporter.initialize();
    FlutterErrorHandler.install();
    runApp(const ProviderScope(child: VelmoraApp()));
  }, (error, stack) {
    ErrorReporter.reportFatal(error, stack);
  });
}

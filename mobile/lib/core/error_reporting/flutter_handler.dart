import 'package:flutter/foundation.dart';
import 'error_reporter.dart';

class FlutterErrorHandler {
  static void install() {
    FlutterError.onError = (FlutterErrorDetails details) {
      FlutterError.presentError(details);
      ErrorReporter.reportFatal(details.exception, details.stack);
    };
    PlatformDispatcher.instance.onError = (error, stack) {
      ErrorReporter.reportFatal(error, stack);
      return true;
    };
  }
}

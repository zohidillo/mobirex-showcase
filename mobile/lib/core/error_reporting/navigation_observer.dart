import 'package:flutter/material.dart';
import 'breadcrumbs.dart';

class BreadcrumbNavigatorObserver extends NavigatorObserver {
  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    BreadcrumbsTracker.addNavigation(
      from: previousRoute?.settings.name ?? '?',
      to: route.settings.name ?? '?',
    );
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    BreadcrumbsTracker.addNavigation(
      from: route.settings.name ?? '?',
      to: previousRoute?.settings.name ?? '?',
    );
  }
}

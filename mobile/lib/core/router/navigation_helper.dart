import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';

void goBack(BuildContext context, WidgetRef ref, {String? fallbackRoute}) {
  if (context.canPop()) {
    context.pop();
    return;
  }
  if (fallbackRoute != null) {
    context.go(fallbackRoute);
    return;
  }
  final user = ref.read(authProvider).user;
  if (user == null) {
    context.go('/login');
  } else if (user.isOwner) {
    context.go('/dashboard');
  } else if (user.isPhoneSeller) {
    context.go('/phones/unsold');
  } else if (user.isAccessorySeller) {
    context.go('/accessories/unsold');
  } else {
    context.go('/login');
  }
}

void handleVelmoraBack(
  BuildContext context,
  WidgetRef ref, {
  String? fallbackRoute,
}) => goBack(context, ref, fallbackRoute: fallbackRoute);

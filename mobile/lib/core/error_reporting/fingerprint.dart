import 'dart:convert';
import 'package:crypto/crypto.dart';

String computeFingerprint({
  required String errorType,
  String? requestPath,
  int? statusCode,
}) {
  final input = '$errorType|${requestPath ?? ''}|${statusCode ?? ''}';
  final digest = sha256.convert(utf8.encode(input));
  return digest.toString().substring(0, 16);
}

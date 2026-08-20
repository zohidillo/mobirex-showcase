import 'package:dio/dio.dart';

import '../../core/utils/safe_debug_log.dart';

String parseApiError(dynamic error) {
  if (error is DioException) {
    if (_isSslError(error)) {
      return 'Server sertifikatida muammo bor.';
    }
    if (_isNetworkError(error)) {
      return 'Internet aloqasi yo‘q. Qayta urinib ko‘ring.';
    }

    final data = error.response?.data;
    if (looksLikeHtml(data)) {
      return 'Server JSON emas, HTML qaytaryapti. Backend URL yoki endpoint noto‘g‘ri bo‘lishi mumkin.';
    }

    final status = error.response?.statusCode;

    if (data is Map) {
      final messages = <String>[];
      for (final entry in data.entries) {
        final value = entry.value;
        if (value is List) {
          messages.add(value.join(' '));
        } else if (value is String) {
          messages.add(value);
        } else if (value is Map) {
          messages.add(value.values.join(' '));
        }
      }
      if (messages.isNotEmpty) return messages.join('\n');
    }
    if (data is String && data.isNotEmpty) return data;

    if (status == 400) return 'Ma’lumotlarni tekshiring.';
    if (status == 401) return 'Sessiya muddati tugadi. Qayta kiring.';
    if (status == 403) return 'Sizga bu amalni bajarish mumkin emas.';
    if (status == 404) return 'Ma’lumot topilmadi.';
    if (status != null && status >= 500) {
      return 'Serverda xatolik yuz berdi. Keyinroq urinib ko‘ring.';
    }

    return 'Noma’lum xatolik yuz berdi.';
  }
  return 'Noma’lum xatolik yuz berdi.';
}

String parseLoginError(dynamic error) {
  if (error is DioException) {
    if (_isSslError(error)) {
      return 'Server sertifikatida muammo bor.';
    }
    if (_isNetworkError(error)) {
      return 'Internet aloqasi yo‘q. Qayta urinib ko‘ring.';
    }

    final data = error.response?.data;
    if (looksLikeHtml(data)) {
      return 'Server JSON emas, HTML qaytaryapti. Backend URL yoki endpoint noto‘g‘ri bo‘lishi mumkin.';
    }

    final status = error.response?.statusCode;
    if (status == 400) {
      return _validationMessage(data) ?? 'Login yoki parol noto‘g‘ri.';
    }
    if (status == 401) {
      // A blocked account also comes back as 401, but with a distinguishing
      // code. Surface the server's calm blocked message instead of the
      // generic wrong-credentials text.
      if (data is Map && data['code'] == 'account_blocked') {
        final detail = data['detail'];
        return detail is String && detail.trim().isNotEmpty
            ? detail
            : 'Hisobingiz vaqtincha to‘xtatilgan. To‘lovni amalga oshiring.';
      }
      return 'Login yoki parol noto‘g‘ri.';
    }
    if (status == 403) return 'Sizga kirish ruxsati yo‘q.';
    if (status == 404) {
      return 'Login API topilmadi. Server sozlamasini tekshiring.';
    }
    if (status != null && status >= 500) {
      return 'Serverda xatolik yuz berdi. Keyinroq urinib ko‘ring.';
    }
  }

  return 'Tizimga kirishda xatolik yuz berdi.';
}

/// True when a login failure is a billing block (401 + code=account_blocked),
/// as opposed to wrong credentials. Lets the login page show the blocked
/// message and a contact button instead of the generic error.
bool isAccountBlockedError(dynamic error) {
  if (error is DioException) {
    final data = error.response?.data;
    return data is Map && data['code'] == 'account_blocked';
  }
  return false;
}

String parsePostLoginProfileError(dynamic error) {
  if (error is DioException && looksLikeHtml(error.response?.data)) {
    return 'Server JSON emas, HTML qaytaryapti. Backend URL yoki endpoint noto‘g‘ri bo‘lishi mumkin.';
  }
  return 'Profil ma’lumotlarini olishda xatolik yuz berdi. Qayta urinib ko‘ring.';
}

bool _isNetworkError(DioException error) {
  return error.type == DioExceptionType.connectionError ||
      error.type == DioExceptionType.connectionTimeout ||
      error.type == DioExceptionType.receiveTimeout ||
      error.type == DioExceptionType.sendTimeout;
}

bool _isSslError(DioException error) {
  final text = '${error.message} ${error.error}'.toLowerCase();
  return text.contains('certificate') ||
      text.contains('handshake') ||
      text.contains('cert_verify') ||
      text.contains('ssl');
}

String? _validationMessage(dynamic data) {
  if (data is Map) {
    final messages = <String>[];
    for (final entry in data.entries) {
      final value = entry.value;
      if (value is List) {
        messages.add(value.join(' '));
      } else if (value is String) {
        messages.add(value);
      } else if (value is Map) {
        messages.add(value.values.join(' '));
      }
    }
    return messages.isEmpty ? null : messages.join('\n');
  }
  return null;
}

import 'package:dio/dio.dart';
import '../models/login_request.dart';
import '../models/pin_response.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/utils/safe_debug_log.dart';
import '../../../profile/data/models/user_model.dart';

class AuthRepository {
  final DioClient _client;

  AuthRepository(this._client);

  Future<void> login(LoginRequest request) async {
    safeAuthLog('Login request URL: ${_urlFor(ApiConstants.login)}');
    try {
      final response = await _client.dio.post(
        ApiConstants.login,
        data: request.toJson(),
      );
      safeAuthLog('Login status: ${response.statusCode}');
      safeAuthLog('Login response keys: ${responseKeysForLog(response.data)}');
      safeAuthLog(
        'Login response body: ${safeResponseBodyForLog(response.data)}',
      );

      final data = response.data;
      if (data is! Map) {
        throw const FormatException('Login response is not a JSON object.');
      }

      final accessToken = data['access'];
      final refreshToken = data['refresh'];
      final hasAccess = accessToken is String && accessToken.isNotEmpty;
      final hasRefresh = refreshToken is String && refreshToken.isNotEmpty;
      safeAuthLog(
        'Login token fields parsed: access=$hasAccess, refresh=$hasRefresh',
      );

      if (!hasAccess || !hasRefresh) {
        throw const FormatException(
          'Login response is missing access or refresh token.',
        );
      }

      await SecureStorageService.saveAccessToken(accessToken);
      await SecureStorageService.saveRefreshToken(refreshToken);
    } on DioException catch (error) {
      _logDioException('Login', error);
      rethrow;
    } catch (error) {
      safeAuthLog('Login parse/storage error: ${error.runtimeType}: $error');
      rethrow;
    }
  }

  Future<UserModel> getMe() async {
    safeAuthLog('/me request URL: ${_urlFor(ApiConstants.me)}');
    try {
      final response = await _client.dio.get(ApiConstants.me);
      safeAuthLog('/me status: ${response.statusCode}');
      safeAuthLog('/me response keys: ${responseKeysForLog(response.data)}');
      return UserModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (error) {
      _logDioException('/me', error);
      rethrow;
    } catch (error) {
      safeAuthLog('/me parse error: ${error.runtimeType}: $error');
      rethrow;
    }
  }

  Future<PinResponse> setPin(String pin) async {
    final response = await _client.dio.post(
      ApiConstants.pinSet,
      data: {'pin': pin},
    );
    return PinResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<PinResponse> verifyPin(String pin) async {
    final response = await _client.dio.post(
      ApiConstants.pinVerify,
      data: {'pin': pin},
    );
    return PinResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<PinResponse> changePin(String oldPin, String newPin) async {
    final response = await _client.dio.post(
      ApiConstants.pinChange,
      data: {'old_pin': oldPin, 'new_pin': newPin},
    );
    return PinResponse.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
    required String newPasswordConfirm,
  }) async {
    await _client.dio.post(
      ApiConstants.changePassword,
      data: {
        'old_password': oldPassword,
        'new_password': newPassword,
        'new_password_confirm': newPasswordConfirm,
      },
    );
  }

  /// Permanently deletes the current user's account (soft-delete on the
  /// backend). The refresh token is sent so the backend can blacklist it.
  /// This does NOT clear local tokens — the caller runs the logout flow on
  /// success so the session is cleared exactly like a normal logout.
  Future<void> deleteAccount() async {
    final refreshToken = await SecureStorageService.getRefreshToken();
    final data = <String, dynamic>{};
    if (refreshToken != null && refreshToken.isNotEmpty) {
      data['refresh'] = refreshToken;
    }
    await _client.dio.post(ApiConstants.accountDelete, data: data);
  }

  Future<void> logout() async {
    await SecureStorageService.clearAll();
  }

  String _urlFor(String path) {
    final baseUrl = _client.dio.options.baseUrl;
    if (baseUrl.endsWith('/') && path.startsWith('/')) {
      return '${baseUrl.substring(0, baseUrl.length - 1)}$path';
    }
    if (!baseUrl.endsWith('/') && !path.startsWith('/')) {
      return '$baseUrl/$path';
    }
    return '$baseUrl$path';
  }

  void _logDioException(String label, DioException error) {
    safeAuthLog('$label DioException type: ${error.type}');
    safeAuthLog('$label request reached backend: ${error.response != null}');
    safeAuthLog('$label status: ${error.response?.statusCode}');
    safeAuthLog(
      '$label response body: ${safeResponseBodyForLog(error.response?.data)}',
    );
  }
}

String parseError(dynamic error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map) {
      final messages = <String>[];
      data.forEach((key, value) {
        if (value is List) {
          messages.add(value.join(' '));
        } else if (value is String) {
          messages.add(value);
        }
      });
      if (messages.isNotEmpty) return messages.join('\n');
    }
    if (data is String) return data;
    return error.message ?? 'Unknown error';
  }
  return error.toString();
}

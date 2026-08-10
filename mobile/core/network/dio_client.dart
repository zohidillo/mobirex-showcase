import 'package:dio/dio.dart';
import '../config/app_config.dart';
import '../error_reporting/api_interceptor.dart';
import 'interceptors/auth_interceptor.dart';

class DioClient {
  late final Dio dio;

  /// Autentifikatsiyasiz chaqiruvlar uchun — `AuthInterceptor` YO'Q.
  ///
  /// Login ekranidagi bog'lanish so'rovi ro'yxatdan o'tmagan odam uchun.
  /// Oddiy `dio` ishlatilsa, qurilmada qolgan eskirgan token so'rovga
  /// qo'shilib, keraksiz refresh/logout oqimini boshlab yuborardi.
  late final Dio publicDio;

  DioClient() {
    dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    dio.interceptors.add(ErrorReportingInterceptor());
    dio.interceptors.add(AuthInterceptor());

    publicDio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    publicDio.interceptors.add(ErrorReportingInterceptor());
  }
}

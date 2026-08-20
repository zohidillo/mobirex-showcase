import 'package:dio/dio.dart';

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../models/contact_request.dart';

/// Ro'yxatdan o'tmagan foydalanuvchi uchun ochiq chaqiruvlar.
///
/// `_client.publicDio` ishlatiladi — `AuthInterceptor` yo'q, ya'ni qurilmada
/// qolgan eskirgan token bu so'rovlarga qo'shilmaydi.
class ContactRepository {
  final DioClient _client;

  ContactRepository(this._client);

  Future<List<RegionModel>> getRegions() async {
    final response = await _client.publicDio.get(ApiConstants.regions);
    final data = response.data;
    if (data is! Map) {
      throw const FormatException('Regions javobi JSON obyekt emas.');
    }
    final payload = data['data'];
    if (payload is! Map) {
      throw const FormatException('Regions javobida "data" yo‘q.');
    }
    final regions = payload['regions'];
    if (regions is! List) {
      throw const FormatException('Regions javobida "regions" ro‘yxati yo‘q.');
    }
    return regions
        .whereType<Map>()
        .map((item) => RegionModel.fromJson(item.cast<String, dynamic>()))
        .where((region) => region.value.isNotEmpty)
        .toList();
  }

  /// Bog'lanish so'rovini yuboradi. Xatolikda `DioException` ko'tariladi.
  Future<void> submitContactRequest(ContactRequest request) async {
    await _client.publicDio.post(
      ApiConstants.publicContactRequest,
      data: request.toJson(),
    );
  }
}

/// Chaqiruvchi ko'rsatadigan xato turi — 429 ni alohida ajratish uchun.
enum ContactRequestFailure { network, rateLimited, validation, unknown }

ContactRequestFailure classifyContactError(Object error) {
  if (error is! DioException) return ContactRequestFailure.unknown;
  final status = error.response?.statusCode;
  if (status == 429) return ContactRequestFailure.rateLimited;
  if (status == 400) return ContactRequestFailure.validation;
  if (error.type == DioExceptionType.connectionError ||
      error.type == DioExceptionType.connectionTimeout ||
      error.type == DioExceptionType.receiveTimeout ||
      error.type == DioExceptionType.sendTimeout) {
    return ContactRequestFailure.network;
  }
  return ContactRequestFailure.unknown;
}

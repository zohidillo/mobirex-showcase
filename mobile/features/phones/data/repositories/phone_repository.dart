import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/paginated_response.dart';
import '../models/phone_model.dart';

class PhoneRepository {
  final DioClient _client;

  PhoneRepository(this._client);

  Future<PaginatedResponse<PhoneModel>> getUnsoldPhones({
    int page = 1,
    String? search,
    int? category,
    String? storage,
    int? branch,
  }) async {
    final params = <String, dynamic>{'page': page};
    if (search != null && search.isNotEmpty) params['q'] = search;
    if (category != null) params['category'] = category;
    if (storage != null && storage.isNotEmpty) params['storage'] = storage;
    if (branch != null) params['branch'] = branch;

    final response = await _client.dio.get(
      ApiConstants.phonesUnsold,
      queryParameters: params,
    );

    return _parsePaginated(response.data);
  }

  Future<PaginatedResponse<PhoneModel>> getSoldPhones({
    int page = 1,
    String? search,
    int? category,
    String? storage,
    int? branch,
    int? year,
    int? month,
  }) async {
    final params = <String, dynamic>{'page': page};
    if (search != null && search.isNotEmpty) params['q'] = search;
    if (category != null) params['category'] = category;
    if (storage != null && storage.isNotEmpty) params['storage'] = storage;
    if (branch != null) params['branch'] = branch;
    if (year != null) params['year'] = year;
    if (month != null) params['month'] = month;

    final response = await _client.dio.get(
      ApiConstants.phonesSold,
      queryParameters: params,
    );

    return _parsePaginated(response.data);
  }

  Future<void> createPhone(Map<String, dynamic> data) async {
    await _client.dio.post(ApiConstants.phones, data: data);
  }

  Future<void> sellPhone(int id, String sellPrice) async {
    await _client.dio.post(
      ApiConstants.phoneSell(id),
      data: {'sell_price': sellPrice},
    );
  }

  Future<void> returnPhone(int id) async {
    await _client.dio.post(ApiConstants.phoneReturn(id), data: {});
  }

  Future<void> deletePhone(int id) async {
    await _client.dio.delete(ApiConstants.phoneDetail(id));
  }

  PaginatedResponse<PhoneModel> _parsePaginated(dynamic raw) {
    final data = raw['data'] as Map<String, dynamic>;
    return PaginatedResponse(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => PhoneModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

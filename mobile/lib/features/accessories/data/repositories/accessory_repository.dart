import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/paginated_response.dart';
import '../models/accessory_model.dart';
import '../models/accessory_sale_model.dart';

class AccessoryRepository {
  final DioClient _client;

  AccessoryRepository(this._client);

  Future<PaginatedResponse<AccessoryModel>> getUnsoldAccessories({
    int page = 1,
    String? search,
    int? category,
    int? branch,
  }) async {
    final params = <String, dynamic>{'page': page};
    if (search != null && search.isNotEmpty) params['q'] = search;
    if (category != null) params['category'] = category;
    if (branch != null) params['branch'] = branch;

    final response = await _client.dio.get(
      ApiConstants.accessoriesUnsold,
      queryParameters: params,
    );
    return _parseAccessories(response.data);
  }

  Future<PaginatedResponse<AccessorySaleModel>> getSoldAccessories({
    int page = 1,
    String? search,
    int? category,
    int? branch,
    int? year,
    int? month,
  }) async {
    final params = <String, dynamic>{'page': page};
    if (search != null && search.isNotEmpty) params['q'] = search;
    if (category != null) params['category'] = category;
    if (branch != null) params['branch'] = branch;
    if (year != null) params['year'] = year;
    if (month != null) params['month'] = month;

    final response = await _client.dio.get(
      ApiConstants.accessoriesSold,
      queryParameters: params,
    );
    return _parseSales(response.data);
  }

  Future<void> createAccessory(Map<String, dynamic> data) async {
    await _client.dio.post(ApiConstants.accessories, data: data);
  }

  Future<void> sellAccessory(int id, int quantity, String totalPrice) async {
    await _client.dio.post(
      ApiConstants.accessorySell(id),
      data: {'quantity': quantity, 'total_price': totalPrice},
    );
  }

  Future<void> returnSale(int saleId) async {
    await _client.dio.post(ApiConstants.accessoryReturn(saleId), data: {});
  }

  Future<void> deleteAccessory(int id) async {
    await _client.dio.delete(ApiConstants.accessoryDetail(id));
  }

  PaginatedResponse<AccessoryModel> _parseAccessories(dynamic raw) {
    final data = raw['data'] as Map<String, dynamic>;
    return PaginatedResponse(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => AccessoryModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  PaginatedResponse<AccessorySaleModel> _parseSales(dynamic raw) {
    final data = raw['data'] as Map<String, dynamic>;
    return PaginatedResponse(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => AccessorySaleModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

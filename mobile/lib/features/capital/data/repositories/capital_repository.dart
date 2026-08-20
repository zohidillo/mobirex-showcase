import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/paginated_response.dart';
import '../models/capital_model.dart';

class CapitalRepository {
  final DioClient _client;
  CapitalRepository(this._client);

  Future<PaginatedResponse<CapitalModel>> getPhoneCapital({
    int? year,
    int? branchId,
    int? page,
  }) async {
    final params = <String, dynamic>{};
    if (year != null) params['year'] = year;
    if (branchId != null) params['branch'] = branchId;
    if (page != null) params['page'] = page;

    final response = await _client.dio.get(
      ApiConstants.phoneCapital,
      queryParameters: params,
    );
    return _parsePage(response.data);
  }

  Future<PaginatedResponse<CapitalModel>> getAccessoryCapital({
    int? year,
    int? branchId,
    int? page,
  }) async {
    final params = <String, dynamic>{};
    if (year != null) params['year'] = year;
    if (branchId != null) params['branch'] = branchId;
    if (page != null) params['page'] = page;

    final response = await _client.dio.get(
      ApiConstants.accessoryCapital,
      queryParameters: params,
    );
    return _parsePage(response.data);
  }

  Future<void> addPhoneCapitalInvestment({
    required int branchId,
    required String amount,
  }) async {
    await _client.dio.post(
      ApiConstants.phoneCapital,
      data: {'branch': branchId, 'amount': amount},
    );
  }

  Future<void> resetPhoneCapital({required int branchId}) async {
    await _client.dio.post(
      ApiConstants.phoneCapitalReset,
      data: {'branch': branchId},
    );
  }

  PaginatedResponse<CapitalModel> _parsePage(dynamic responseData) {
    final data = responseData['data'] as Map<String, dynamic>;
    return PaginatedResponse<CapitalModel>(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => CapitalModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

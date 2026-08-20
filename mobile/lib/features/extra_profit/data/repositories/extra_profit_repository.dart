import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/paginated_response.dart';
import '../models/extra_profit_model.dart';

class ExtraProfitRepository {
  final DioClient _client;
  ExtraProfitRepository(this._client);

  Future<PaginatedResponse<ExtraProfitModel>> getExtraProfits({
    int page = 1,
    String? search,
    int? year,
    int? month,
    int? branch,
  }) async {
    final params = <String, dynamic>{'page': page};
    if (search != null && search.isNotEmpty) params['q'] = search;
    if (year != null) params['year'] = year;
    if (month != null) params['month'] = month;
    if (branch != null) params['branch'] = branch;

    final response = await _client.dio.get(
      ApiConstants.extraProfits,
      queryParameters: params,
    );
    final data = response.data['data'] as Map<String, dynamic>;
    return PaginatedResponse(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => ExtraProfitModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Future<void> createExtraProfit({required String amount, String? note}) async {
    await _client.dio.post(
      ApiConstants.extraProfits,
      data: {
        'amount': amount,
        if (note != null && note.isNotEmpty) 'note': note,
      },
    );
  }

  Future<void> deleteExtraProfit(int id) async {
    await _client.dio.delete(ApiConstants.extraProfitDetail(id));
  }
}

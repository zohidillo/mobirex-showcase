import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/paginated_response.dart';
import '../models/debt_model.dart';

class DebtRepository {
  final DioClient _client;

  DebtRepository(this._client);

  Future<PaginatedResponse<DebtModel>> getDebts({
    int page = 1,
    String? search,
    String? direction,
    int? year,
    int? month,
    int? branch,
    String? domain,
  }) async {
    final params = <String, dynamic>{'page': page};
    if (search != null && search.isNotEmpty) params['q'] = search;
    if (direction != null) params['type'] = direction;
    if (year != null) params['year'] = year;
    if (month != null) params['month'] = month;
    if (branch != null) params['branch'] = branch;
    if (domain != null) params['domain'] = domain;

    final response = await _client.dio.get(
      ApiConstants.debts,
      queryParameters: params,
    );
    return _parsePaginated(response.data);
  }

  Future<PaginatedResponse<DebtModel>> getClosedDebts({
    int page = 1,
    String? search,
    String? direction,
    int? year,
    int? month,
    int? branch,
    String? domain,
  }) async {
    final params = <String, dynamic>{'page': page};
    if (search != null && search.isNotEmpty) params['q'] = search;
    if (direction != null) params['type'] = direction;
    if (year != null) params['year'] = year;
    if (month != null) params['month'] = month;
    if (branch != null) params['branch'] = branch;
    if (domain != null) params['domain'] = domain;

    final response = await _client.dio.get(
      ApiConstants.closedDebts,
      queryParameters: params,
    );
    return _parsePaginated(response.data);
  }

  Future<DebtModel> createDebt({
    required String fName,
    required String amount,
    required String direction,
    String? note,
  }) async {
    final response = await _client.dio.post(
      ApiConstants.debts,
      data: {
        'f_name': fName,
        'amount': amount,
        'direction': direction,
        if (note != null && note.isNotEmpty) 'note': note,
      },
    );
    return DebtModel.fromJson(response.data['data'] as Map<String, dynamic>);
  }

  Future<DebtPayment> payDebt(int id, String amount, {String? note}) async {
    final response = await _client.dio.post(
      ApiConstants.debtPay(id),
      data: {
        'amount': amount,
        if (note != null && note.isNotEmpty) 'note': note,
      },
    );
    return DebtPayment.fromJson(response.data['data'] as Map<String, dynamic>);
  }

  Future<void> deleteDebt(int id) async {
    await _client.dio.delete(ApiConstants.debtDetail(id));
  }

  Future<PaginatedResponse<DebtPayment>> getDebtPayments({
    required int debtId,
  }) async {
    final response = await _client.dio.get(
      ApiConstants.debtPayments,
      queryParameters: {'debt': debtId},
    );
    final data = response.data['data'] as Map<String, dynamic>;
    return PaginatedResponse(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => DebtPayment.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Future<void> deletePayment(int paymentId) async {
    await _client.dio.delete(ApiConstants.debtPaymentDetail(paymentId));
  }

  PaginatedResponse<DebtModel> _parsePaginated(dynamic raw) {
    final data = raw['data'] as Map<String, dynamic>;
    return PaginatedResponse(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => DebtModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

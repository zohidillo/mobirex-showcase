import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/paginated_response.dart';
import '../models/expense_model.dart';

class ExpensePageResult {
  final PaginatedResponse<ExpenseModel> page;
  final String? totalAmount;
  const ExpensePageResult({required this.page, this.totalAmount});
}

class ExpenseRepository {
  final DioClient _client;
  ExpenseRepository(this._client);

  Future<ExpensePageResult> getExpenses({
    int page = 1,
    String? type,
    int? year,
    int? month,
    int? branch,
  }) async {
    final params = <String, dynamic>{'page': page};
    if (type != null && type.isNotEmpty) params['type'] = type;
    if (year != null) params['year'] = year;
    if (month != null) params['month'] = month;
    if (branch != null) params['branch'] = branch;

    final response = await _client.dio.get(
      ApiConstants.expenses,
      queryParameters: params,
    );
    final data = response.data['data'] as Map<String, dynamic>;
    final paginated = PaginatedResponse<ExpenseModel>(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => ExpenseModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
    return ExpensePageResult(
      page: paginated,
      totalAmount: data['total_amount'] as String?,
    );
  }

  Future<void> createExpense({
    required String type,
    required String amount,
    String? note,
  }) async {
    await _client.dio.post(
      ApiConstants.expenses,
      data: {
        'type': type,
        'amount': amount,
        if (note != null && note.isNotEmpty) 'note': note,
      },
    );
  }

  Future<void> deleteExpense(int id) async {
    await _client.dio.delete(ApiConstants.expenseDetail(id));
  }
}

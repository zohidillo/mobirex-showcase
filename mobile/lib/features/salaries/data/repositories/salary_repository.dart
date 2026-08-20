import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/paginated_response.dart';
import '../models/salary_model.dart';
import '../models/staff_model.dart';

class SalaryRepository {
  final DioClient _client;
  SalaryRepository(this._client);

  Future<PaginatedResponse<SalaryModel>> getSalaries({
    int page = 1,
    int? year,
    int? month,
    int? branch,
    int? employee,
  }) async {
    final params = <String, dynamic>{'page': page};
    if (year != null) params['year'] = year;
    if (month != null) params['month'] = month;
    if (branch != null) params['branch'] = branch;
    if (employee != null) params['employee'] = employee;

    final response = await _client.dio.get(
      ApiConstants.salaries,
      queryParameters: params,
    );
    final data = response.data['data'] as Map<String, dynamic>;
    return PaginatedResponse(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => SalaryModel.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Future<void> createSalary({
    required int employeeId,
    required String amount,
    String? note,
  }) async {
    await _client.dio.post(
      ApiConstants.salaries,
      data: {
        'employee': employeeId,
        'amount': amount,
        if (note != null && note.isNotEmpty) 'note': note,
      },
    );
  }

  Future<void> deleteSalary(int id) async {
    await _client.dio.delete(ApiConstants.salaryDetail(id));
  }

  Future<List<StaffMember>> getStaff({int? branchId}) async {
    final params = <String, dynamic>{};
    if (branchId != null) params['branch'] = branchId;
    final response = await _client.dio.get(
      ApiConstants.ownerStaff,
      queryParameters: params,
    );
    final raw = response.data['data'];
    if (raw is List) {
      return raw
          .map((e) => StaffMember.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }
}

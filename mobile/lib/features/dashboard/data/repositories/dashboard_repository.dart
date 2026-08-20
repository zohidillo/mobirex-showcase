import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../features/salaries/data/models/staff_model.dart';
import '../models/dashboard_model.dart';

class DashboardRepository {
  final DioClient _client;

  DashboardRepository(this._client);

  Future<DashboardModel> getDashboard({
    required int branchId,
    required String role,
    int? staffId,
    required int year,
    required int month,
  }) async {
    final params = <String, dynamic>{
      'branch_id': branchId,
      'role': role,
      'year': year,
      'month': month,
    };
    if (staffId != null) params['staff_id'] = staffId;

    final response = await _client.dio.get(
      ApiConstants.dashboardStaff,
      queryParameters: params,
    );

    final data = response.data['data'] as Map<String, dynamic>;
    return DashboardModel.fromJson(data);
  }

  Future<List<StaffMember>> getStaff(int branchId) async {
    final response = await _client.dio.get(
      ApiConstants.ownerStaff,
      queryParameters: {'branch': branchId},
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

import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/paginated_response.dart';
import '../models/support_message_model.dart';
import '../models/support_request_model.dart';

class SupportRepository {
  final DioClient _client;

  SupportRepository(this._client);

  Future<PaginatedResponse<SupportRequest>> getRequests({int page = 1}) async {
    final response = await _client.dio.get(
      ApiConstants.supportRequests,
      queryParameters: {'page': page},
    );
    final data = response.data['data'] as Map<String, dynamic>;
    return PaginatedResponse(
      count: data['count'] as int,
      next: data['next'] as String?,
      previous: data['previous'] as String?,
      results: (data['results'] as List<dynamic>)
          .map((e) => SupportRequest.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Future<SupportRequest> getRequest(int id) async {
    final response = await _client.dio.get(
      ApiConstants.supportRequestDetail(id),
    );
    return SupportRequest.fromJson(
      response.data['data'] as Map<String, dynamic>,
    );
  }

  Future<SupportRequest> createRequest({
    required String requestType,
    required String source,
    required String phone,
    required String message,
  }) async {
    final response = await _client.dio.post(
      ApiConstants.supportRequests,
      data: {
        'request_type': requestType,
        'source': source,
        'phone': phone,
        'message': message,
      },
    );
    return SupportRequest.fromJson(
      response.data['data'] as Map<String, dynamic>,
    );
  }

  Future<SupportMessage> sendMessage(int requestId, String message) async {
    final response = await _client.dio.post(
      ApiConstants.supportRequestMessages(requestId),
      data: {'message': message},
    );
    final raw = response.data;
    if (raw is Map && raw.containsKey('data') && raw['data'] is Map) {
      return SupportMessage.fromJson(raw['data'] as Map<String, dynamic>);
    }
    return SupportMessage.fromJson(raw as Map<String, dynamic>);
  }
}

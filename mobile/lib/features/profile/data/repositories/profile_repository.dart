import '../../../../core/constants/api_constants.dart';
import '../../../../core/network/dio_client.dart';
import '../models/user_model.dart';

class ProfileRepository {
  final DioClient _client;

  ProfileRepository(this._client);

  Future<UserModel> getMe() async {
    final response = await _client.dio.get(ApiConstants.me);
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<UserModel> updateSettings(Map<String, dynamic> settings) async {
    final response = await _client.dio.patch(
      ApiConstants.meSettings,
      data: settings,
    );
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }
}

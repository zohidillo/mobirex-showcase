import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../../core/network/dio_providers.dart';
import '../../data/repositories/profile_repository.dart';

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepository(ref.read(dioClientProvider));
});

class ProfileActionNotifier extends StateNotifier<AsyncValue<void>> {
  final ProfileRepository _repo;
  final AuthNotifier _auth;

  ProfileActionNotifier(this._repo, this._auth) : super(const AsyncData(null));

  Future<bool> updateTheme(String theme) async {
    state = const AsyncLoading();
    try {
      final updated = await _repo.updateSettings({'theme': theme});
      await _auth.updateUser(updated);
      state = const AsyncData(null);
      return true;
    } catch (e) {
      state = AsyncError(e, StackTrace.current);
      return false;
    }
  }

  Future<bool> updateUsername(String username) async {
    state = const AsyncLoading();
    try {
      final updated = await _repo.updateSettings({'username': username});
      await _auth.updateUser(updated);
      state = const AsyncData(null);
      return true;
    } catch (e) {
      state = AsyncError(e, StackTrace.current);
      return false;
    }
  }
}

final profileActionProvider =
    StateNotifierProvider<ProfileActionNotifier, AsyncValue<void>>((ref) {
      return ProfileActionNotifier(
        ref.read(profileRepositoryProvider),
        ref.read(authProvider.notifier),
      );
    });

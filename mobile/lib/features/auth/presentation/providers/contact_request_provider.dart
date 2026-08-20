import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/dio_providers.dart';
import '../../data/models/contact_request.dart';
import '../../data/repositories/contact_repository.dart';

final contactRepositoryProvider = Provider<ContactRepository>(
  (ref) => ContactRepository(ref.watch(dioClientProvider)),
);

/// Viloyatlar — sessiya davomida bir marta olinadi va xotirada saqlanadi.
/// `autoDispose` YO'Q: ekran yopilib qayta ochilsa qayta so'ralmasin.
final regionsProvider = FutureProvider<List<RegionModel>>(
  (ref) => ref.watch(contactRepositoryProvider).getRegions(),
);

enum ContactRequestStatus { idle, submitting, success, error }

class ContactRequestState {
  const ContactRequestState({
    this.status = ContactRequestStatus.idle,
    this.error,
  });

  final ContactRequestStatus status;
  final String? error;

  bool get isSubmitting => status == ContactRequestStatus.submitting;
  bool get isSuccess => status == ContactRequestStatus.success;
}

class ContactRequestNotifier extends StateNotifier<ContactRequestState> {
  ContactRequestNotifier(this._repository)
    : super(const ContactRequestState());

  final ContactRepository _repository;

  Future<void> submit({required String phone, required String region}) async {
    if (state.isSubmitting) return;
    state = const ContactRequestState(status: ContactRequestStatus.submitting);
    try {
      await _repository.submitContactRequest(
        ContactRequest(phone: phone, region: region),
      );
      state = const ContactRequestState(status: ContactRequestStatus.success);
    } catch (error) {
      state = ContactRequestState(
        status: ContactRequestStatus.error,
        error: _messageFor(error),
      );
    }
  }

  void reset() => state = const ContactRequestState();

  String _messageFor(Object error) {
    switch (classifyContactError(error)) {
      case ContactRequestFailure.rateLimited:
        return "Juda ko'p urinish bo'ldi. Biroz kutib, qayta urinib ko'ring.";
      case ContactRequestFailure.network:
        return "Internet aloqasi yo'q. Ulanishni tekshirib, qayta urinib ko'ring.";
      case ContactRequestFailure.validation:
        return _serverMessage(error) ??
            "Ma'lumotlarni tekshiring va qayta urinib ko'ring.";
      case ContactRequestFailure.unknown:
        return "Yuborishda xatolik yuz berdi. Qayta urinib ko'ring.";
    }
  }

  /// Backend konverti: `{success, data, error}` — `error` matn bo'ladi.
  String? _serverMessage(Object error) {
    if (error is! DioException) return null;
    final data = error.response?.data;
    if (data is Map) {
      final message = data['error'];
      if (message is String && message.trim().isNotEmpty) return message;
    }
    return null;
  }
}

/// `autoDispose` — ekran yopilganda holat tozalanadi. Aks holda muvaffaqiyat
/// ekrani yopishib qolardi: foydalanuvchi tizim "orqaga" tugmasi bilan
/// chiqib, qaytib kirsa, forma o'rniga eski tasdiqni ko'rardi.
final contactRequestProvider =
    StateNotifierProvider.autoDispose<
      ContactRequestNotifier,
      ContactRequestState
    >((ref) => ContactRequestNotifier(ref.watch(contactRepositoryProvider)));

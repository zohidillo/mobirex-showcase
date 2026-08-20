import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/dio_providers.dart';
import '../../data/models/support_message_model.dart';
import '../../data/models/support_request_model.dart';
import '../../data/repositories/support_repository.dart';
import '../../../../shared/utils/error_parser.dart';

final supportRepositoryProvider = Provider<SupportRepository>((ref) {
  return SupportRepository(ref.read(dioClientProvider));
});

// ---------------------------------------------------------------------------
// List
// ---------------------------------------------------------------------------

class SupportListState {
  final List<SupportRequest> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final String? error;

  const SupportListState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
  });

  SupportListState copyWith({
    List<SupportRequest>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    String? error,
    bool clearError = false,
  }) => SupportListState(
    items: items ?? this.items,
    isLoading: isLoading ?? this.isLoading,
    isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    hasMore: hasMore ?? this.hasMore,
    page: page ?? this.page,
    error: clearError ? null : (error ?? this.error),
  );
}

final supportListProvider =
    StateNotifierProvider<SupportListNotifier, SupportListState>((ref) {
      return SupportListNotifier(ref.read(supportRepositoryProvider));
    });

class SupportListNotifier extends StateNotifier<SupportListState> {
  final SupportRepository _repo;

  SupportListNotifier(this._repo) : super(const SupportListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? const SupportListState(isLoading: true)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final resp = await _repo.getRequests(page: refresh ? 1 : state.page);
      state = state.copyWith(
        items: refresh ? resp.results : [...state.items, ...resp.results],
        isLoading: false,
        hasMore: resp.hasMore,
        page: (refresh ? 1 : state.page) + 1,
        clearError: true,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: parseApiError(e));
    }
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || !state.hasMore || state.isLoading) return;
    state = state.copyWith(isLoadingMore: true);
    try {
      final resp = await _repo.getRequests(page: state.page);
      state = state.copyWith(
        items: [...state.items, ...resp.results],
        isLoadingMore: false,
        hasMore: resp.hasMore,
        page: state.page + 1,
        clearError: true,
      );
    } catch (e) {
      state = state.copyWith(isLoadingMore: false, error: parseApiError(e));
    }
  }
}

// ---------------------------------------------------------------------------
// Detail
// ---------------------------------------------------------------------------

class SupportDetailState {
  final SupportRequest? request;
  final List<SupportMessage> messages;
  final bool isLoading;
  final bool isSending;
  final String? error;
  final String? sendError;

  const SupportDetailState({
    this.request,
    this.messages = const [],
    this.isLoading = true,
    this.isSending = false,
    this.error,
    this.sendError,
  });

  SupportDetailState copyWith({
    SupportRequest? request,
    List<SupportMessage>? messages,
    bool? isLoading,
    bool? isSending,
    String? error,
    String? sendError,
    bool clearError = false,
    bool clearSendError = false,
  }) => SupportDetailState(
    request: request ?? this.request,
    messages: messages ?? this.messages,
    isLoading: isLoading ?? this.isLoading,
    isSending: isSending ?? this.isSending,
    error: clearError ? null : (error ?? this.error),
    sendError: clearSendError ? null : (sendError ?? this.sendError),
  );
}

final supportDetailProvider =
    StateNotifierProvider.family<
      SupportDetailNotifier,
      SupportDetailState,
      int
    >(
      (ref, id) =>
          SupportDetailNotifier(ref.read(supportRepositoryProvider), ref, id),
    );

class SupportDetailNotifier extends StateNotifier<SupportDetailState> {
  final SupportRepository _repo;
  final Ref _ref;
  final int _id;

  SupportDetailNotifier(this._repo, this._ref, this._id)
    : super(const SupportDetailState()) {
    load();
  }

  Future<void> load() async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final request = await _repo.getRequest(_id);
      state = state.copyWith(
        request: request,
        messages: request.messages,
        isLoading: false,
      );
      _ref.read(supportListProvider.notifier).load(refresh: true);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: "Murojaat ma'lumotlarini yuklab bo'lmadi.",
      );
    }
  }

  Future<String?> sendMessage(String message) async {
    state = state.copyWith(isSending: true, clearSendError: true);
    try {
      await _repo.sendMessage(_id, message);
      final updated = await _repo.getRequest(_id);
      state = state.copyWith(
        request: updated,
        messages: updated.messages,
        isSending: false,
      );
      _ref.read(supportListProvider.notifier).load(refresh: true);
      return null;
    } catch (e) {
      state = state.copyWith(isSending: false, sendError: parseApiError(e));
      return parseApiError(e);
    }
  }
}

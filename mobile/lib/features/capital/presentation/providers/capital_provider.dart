import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_providers.dart';
import '../../data/models/capital_model.dart';
import '../../data/repositories/capital_repository.dart';
import '../../../../shared/utils/error_parser.dart';

final capitalRepositoryProvider = Provider<CapitalRepository>((ref) {
  return CapitalRepository(ref.read(dioClientProvider));
});

// ---------------------------------------------------------------------------
// Filter
// ---------------------------------------------------------------------------

class CapitalFilter {
  final int? year;
  final int? branchId;

  const CapitalFilter({this.year, this.branchId});

  CapitalFilter copyWith({
    int? year,
    int? branchId,
    bool clearYear = false,
    bool clearBranch = false,
  }) => CapitalFilter(
    year: clearYear ? null : (year ?? this.year),
    branchId: clearBranch ? null : (branchId ?? this.branchId),
  );
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

class CapitalListState {
  final List<CapitalModel> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final String? error;
  final CapitalFilter filter;

  const CapitalListState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
    this.filter = const CapitalFilter(),
  });

  CapitalListState copyWith({
    List<CapitalModel>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    String? error,
    CapitalFilter? filter,
    bool clearError = false,
  }) => CapitalListState(
    items: items ?? this.items,
    isLoading: isLoading ?? this.isLoading,
    isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    hasMore: hasMore ?? this.hasMore,
    page: page ?? this.page,
    error: clearError ? null : (error ?? this.error),
    filter: filter ?? this.filter,
  );
}

// ---------------------------------------------------------------------------
// Phone Capital
// ---------------------------------------------------------------------------

final phoneCapitalProvider =
    StateNotifierProvider<PhoneCapitalNotifier, CapitalListState>((ref) {
      return PhoneCapitalNotifier(ref.read(capitalRepositoryProvider));
    });

class PhoneCapitalNotifier extends StateNotifier<CapitalListState> {
  final CapitalRepository _repo;

  PhoneCapitalNotifier(this._repo) : super(const CapitalListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? CapitalListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final resp = await _repo.getPhoneCapital(
        year: state.filter.year,
        branchId: state.filter.branchId,
        page: refresh ? 1 : state.page,
      );
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
      final resp = await _repo.getPhoneCapital(
        year: state.filter.year,
        branchId: state.filter.branchId,
        page: state.page,
      );
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

  void applyFilter(CapitalFilter filter) {
    state = CapitalListState(filter: filter);
    load();
  }

  Future<String?> addInvestment({
    required int branchId,
    required String amount,
  }) async {
    try {
      await _repo.addPhoneCapitalInvestment(branchId: branchId, amount: amount);
      await load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }

  Future<String?> resetCapital({required int branchId}) async {
    try {
      await _repo.resetPhoneCapital(branchId: branchId);
      await load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

// ---------------------------------------------------------------------------
// Accessory Capital
// ---------------------------------------------------------------------------

final accessoryCapitalProvider =
    StateNotifierProvider<AccessoryCapitalNotifier, CapitalListState>((ref) {
      return AccessoryCapitalNotifier(ref.read(capitalRepositoryProvider));
    });

class AccessoryCapitalNotifier extends StateNotifier<CapitalListState> {
  final CapitalRepository _repo;

  AccessoryCapitalNotifier(this._repo) : super(const CapitalListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? CapitalListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final resp = await _repo.getAccessoryCapital(
        year: state.filter.year,
        branchId: state.filter.branchId,
        page: refresh ? 1 : state.page,
      );
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
      final resp = await _repo.getAccessoryCapital(
        year: state.filter.year,
        branchId: state.filter.branchId,
        page: state.page,
      );
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

  void applyFilter(CapitalFilter filter) {
    state = CapitalListState(filter: filter);
    load();
  }
}

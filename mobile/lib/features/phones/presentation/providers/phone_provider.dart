import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_providers.dart';
import '../../data/models/phone_model.dart';
import '../../data/repositories/phone_repository.dart';
import '../../../../shared/utils/error_parser.dart';

final phoneRepositoryProvider = Provider<PhoneRepository>((ref) {
  return PhoneRepository(ref.read(dioClientProvider));
});

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

class PhoneFilter {
  final String? search;
  final int? category;
  final String? storage;
  final int? branch;
  final int? year;
  final int? month;

  const PhoneFilter({
    this.search,
    this.category,
    this.storage,
    this.branch,
    this.year,
    this.month,
  });

  PhoneFilter copyWith({
    String? search,
    int? category,
    String? storage,
    int? branch,
    int? year,
    int? month,
    bool clearSearch = false,
    bool clearCategory = false,
    bool clearStorage = false,
    bool clearBranch = false,
    bool clearYearMonth = false,
  }) => PhoneFilter(
    search: clearSearch ? null : (search ?? this.search),
    category: clearCategory ? null : (category ?? this.category),
    storage: clearStorage ? null : (storage ?? this.storage),
    branch: clearBranch ? null : (branch ?? this.branch),
    year: clearYearMonth ? null : (year ?? this.year),
    month: clearYearMonth ? null : (month ?? this.month),
  );
}

class PhoneListState {
  final List<PhoneModel> phones;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final String? error;
  final PhoneFilter filter;

  const PhoneListState({
    this.phones = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
    this.filter = const PhoneFilter(),
  });

  PhoneListState copyWith({
    List<PhoneModel>? phones,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    String? error,
    PhoneFilter? filter,
    bool clearError = false,
  }) => PhoneListState(
    phones: phones ?? this.phones,
    isLoading: isLoading ?? this.isLoading,
    isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    hasMore: hasMore ?? this.hasMore,
    page: page ?? this.page,
    error: clearError ? null : (error ?? this.error),
    filter: filter ?? this.filter,
  );

  Set<PhoneCategory> get categories =>
      phones.where((p) => p.category != null).map((p) => p.category!).toSet();
}

// ---------------------------------------------------------------------------
// Unsold phones
// ---------------------------------------------------------------------------

final unsoldPhonesProvider =
    StateNotifierProvider<UnsoldPhonesNotifier, PhoneListState>((ref) {
      return UnsoldPhonesNotifier(ref.read(phoneRepositoryProvider), ref);
    });

class UnsoldPhonesNotifier extends StateNotifier<PhoneListState> {
  final PhoneRepository _repo;
  final Ref _ref;

  UnsoldPhonesNotifier(this._repo, this._ref) : super(const PhoneListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;

    state = refresh
        ? PhoneListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.phones.isEmpty);

    try {
      final resp = await _repo.getUnsoldPhones(
        page: refresh ? 1 : state.page,
        search: state.filter.search,
        category: state.filter.category,
        storage: state.filter.storage,
        branch: state.filter.branch,
      );

      state = state.copyWith(
        phones: refresh ? resp.results : [...state.phones, ...resp.results],
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
      final resp = await _repo.getUnsoldPhones(
        page: state.page,
        search: state.filter.search,
        category: state.filter.category,
        storage: state.filter.storage,
        branch: state.filter.branch,
      );
      state = state.copyWith(
        phones: [...state.phones, ...resp.results],
        isLoadingMore: false,
        hasMore: resp.hasMore,
        page: state.page + 1,
        clearError: true,
      );
    } catch (e) {
      state = state.copyWith(isLoadingMore: false, error: parseApiError(e));
    }
  }

  void applyFilter(PhoneFilter filter) {
    state = PhoneListState(filter: filter);
    load();
  }

  Future<String?> sellPhone(int id, String sellPrice) async {
    try {
      await _repo.sellPhone(id, sellPrice);
      state = state.copyWith(
        phones: state.phones.where((p) => p.id != id).toList(),
      );
      _ref.read(soldPhonesProvider.notifier).load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }

  Future<String?> deletePhone(int id) async {
    try {
      await _repo.deletePhone(id);
      state = state.copyWith(
        phones: state.phones.where((p) => p.id != id).toList(),
      );
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

// ---------------------------------------------------------------------------
// Sold phones
// ---------------------------------------------------------------------------

final soldPhonesProvider =
    StateNotifierProvider<SoldPhonesNotifier, PhoneListState>((ref) {
      return SoldPhonesNotifier(ref.read(phoneRepositoryProvider), ref);
    });

class SoldPhonesNotifier extends StateNotifier<PhoneListState> {
  final PhoneRepository _repo;
  final Ref _ref;

  SoldPhonesNotifier(this._repo, this._ref) : super(const PhoneListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;

    state = refresh
        ? PhoneListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.phones.isEmpty);

    try {
      final resp = await _repo.getSoldPhones(
        page: refresh ? 1 : state.page,
        search: state.filter.search,
        category: state.filter.category,
        storage: state.filter.storage,
        branch: state.filter.branch,
        year: state.filter.year,
        month: state.filter.month,
      );

      state = state.copyWith(
        phones: refresh ? resp.results : [...state.phones, ...resp.results],
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
      final resp = await _repo.getSoldPhones(
        page: state.page,
        search: state.filter.search,
        category: state.filter.category,
        storage: state.filter.storage,
        branch: state.filter.branch,
        year: state.filter.year,
        month: state.filter.month,
      );
      state = state.copyWith(
        phones: [...state.phones, ...resp.results],
        isLoadingMore: false,
        hasMore: resp.hasMore,
        page: state.page + 1,
        clearError: true,
      );
    } catch (e) {
      state = state.copyWith(isLoadingMore: false, error: parseApiError(e));
    }
  }

  void applyFilter(PhoneFilter filter) {
    state = PhoneListState(filter: filter);
    load();
  }

  Future<String?> returnPhone(int id) async {
    try {
      await _repo.returnPhone(id);
      state = state.copyWith(
        phones: state.phones.where((p) => p.id != id).toList(),
      );
      _ref.read(unsoldPhonesProvider.notifier).load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

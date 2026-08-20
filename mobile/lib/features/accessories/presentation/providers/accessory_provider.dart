import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_providers.dart';
import '../../data/models/accessory_model.dart';
import '../../data/models/accessory_sale_model.dart';
import '../../data/repositories/accessory_repository.dart';
import '../../../../shared/utils/error_parser.dart';

final accessoryRepositoryProvider = Provider<AccessoryRepository>((ref) {
  return AccessoryRepository(ref.read(dioClientProvider));
});

// ---------------------------------------------------------------------------
// Filter
// ---------------------------------------------------------------------------

class AccessoryFilter {
  final String? search;
  final int? category;
  final int? branch;
  final int? year;
  final int? month;

  const AccessoryFilter({
    this.search,
    this.category,
    this.branch,
    this.year,
    this.month,
  });

  AccessoryFilter copyWith({
    String? search,
    int? category,
    int? branch,
    int? year,
    int? month,
    bool clearSearch = false,
    bool clearCategory = false,
    bool clearBranch = false,
    bool clearYearMonth = false,
  }) => AccessoryFilter(
    search: clearSearch ? null : (search ?? this.search),
    category: clearCategory ? null : (category ?? this.category),
    branch: clearBranch ? null : (branch ?? this.branch),
    year: clearYearMonth ? null : (year ?? this.year),
    month: clearYearMonth ? null : (month ?? this.month),
  );
}

// ---------------------------------------------------------------------------
// Unsold accessories state
// ---------------------------------------------------------------------------

class AccessoryListState {
  final List<AccessoryModel> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final String? error;
  final AccessoryFilter filter;

  const AccessoryListState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
    this.filter = const AccessoryFilter(),
  });

  AccessoryListState copyWith({
    List<AccessoryModel>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    String? error,
    AccessoryFilter? filter,
    bool clearError = false,
  }) => AccessoryListState(
    items: items ?? this.items,
    isLoading: isLoading ?? this.isLoading,
    isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    hasMore: hasMore ?? this.hasMore,
    page: page ?? this.page,
    error: clearError ? null : (error ?? this.error),
    filter: filter ?? this.filter,
  );

  Set<AccessoryCategory> get categories =>
      items.where((a) => a.category != null).map((a) => a.category!).toSet();
}

final unsoldAccessoriesProvider =
    StateNotifierProvider<UnsoldAccessoriesNotifier, AccessoryListState>((ref) {
      return UnsoldAccessoriesNotifier(
        ref.read(accessoryRepositoryProvider),
        ref,
      );
    });

class UnsoldAccessoriesNotifier extends StateNotifier<AccessoryListState> {
  final AccessoryRepository _repo;
  final Ref _ref;

  UnsoldAccessoriesNotifier(this._repo, this._ref)
    : super(const AccessoryListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? AccessoryListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final resp = await _repo.getUnsoldAccessories(
        page: refresh ? 1 : state.page,
        search: state.filter.search,
        category: state.filter.category,
        branch: state.filter.branch,
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
      final resp = await _repo.getUnsoldAccessories(
        page: state.page,
        search: state.filter.search,
        category: state.filter.category,
        branch: state.filter.branch,
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

  void applyFilter(AccessoryFilter filter) {
    state = AccessoryListState(filter: filter);
    load();
  }

  Future<String?> sellAccessory(int id, int quantity, String totalPrice) async {
    try {
      await _repo.sellAccessory(id, quantity, totalPrice);
      await load(refresh: true);
      _ref.read(soldAccessoriesProvider.notifier).load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }

  Future<String?> deleteAccessory(int id) async {
    try {
      await _repo.deleteAccessory(id);
      state = state.copyWith(
        items: state.items.where((a) => a.id != id).toList(),
      );
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

// ---------------------------------------------------------------------------
// Sold accessories state
// ---------------------------------------------------------------------------

class SoldAccessoryListState {
  final List<AccessorySaleModel> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final String? error;
  final AccessoryFilter filter;

  const SoldAccessoryListState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
    this.filter = const AccessoryFilter(),
  });

  SoldAccessoryListState copyWith({
    List<AccessorySaleModel>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    String? error,
    AccessoryFilter? filter,
    bool clearError = false,
  }) => SoldAccessoryListState(
    items: items ?? this.items,
    isLoading: isLoading ?? this.isLoading,
    isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    hasMore: hasMore ?? this.hasMore,
    page: page ?? this.page,
    error: clearError ? null : (error ?? this.error),
    filter: filter ?? this.filter,
  );
}

final soldAccessoriesProvider =
    StateNotifierProvider<SoldAccessoriesNotifier, SoldAccessoryListState>((
      ref,
    ) {
      return SoldAccessoriesNotifier(
        ref.read(accessoryRepositoryProvider),
        ref,
      );
    });

class SoldAccessoriesNotifier extends StateNotifier<SoldAccessoryListState> {
  final AccessoryRepository _repo;
  final Ref _ref;

  SoldAccessoriesNotifier(this._repo, this._ref)
    : super(const SoldAccessoryListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? SoldAccessoryListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final resp = await _repo.getSoldAccessories(
        page: refresh ? 1 : state.page,
        search: state.filter.search,
        category: state.filter.category,
        branch: state.filter.branch,
        year: state.filter.year,
        month: state.filter.month,
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
      final resp = await _repo.getSoldAccessories(
        page: state.page,
        search: state.filter.search,
        category: state.filter.category,
        branch: state.filter.branch,
        year: state.filter.year,
        month: state.filter.month,
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

  void applyFilter(AccessoryFilter filter) {
    state = SoldAccessoryListState(filter: filter);
    load();
  }

  Future<String?> returnSale(int saleId) async {
    try {
      await _repo.returnSale(saleId);
      state = state.copyWith(
        items: state.items.where((s) => s.id != saleId).toList(),
      );
      _ref.read(unsoldAccessoriesProvider.notifier).load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

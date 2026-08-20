import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_providers.dart';
import '../../data/models/extra_profit_model.dart';
import '../../data/repositories/extra_profit_repository.dart';
import '../../../../shared/utils/error_parser.dart';

final extraProfitRepositoryProvider = Provider<ExtraProfitRepository>((ref) {
  return ExtraProfitRepository(ref.read(dioClientProvider));
});

// ---------------------------------------------------------------------------
// Filter
// ---------------------------------------------------------------------------

class ExtraProfitFilter {
  final String? search;
  final int? year;
  final int? month;
  final int? branch;

  const ExtraProfitFilter({this.search, this.year, this.month, this.branch});

  ExtraProfitFilter copyWith({
    String? search,
    int? year,
    int? month,
    int? branch,
    bool clearSearch = false,
    bool clearYearMonth = false,
    bool clearBranch = false,
  }) => ExtraProfitFilter(
    search: clearSearch ? null : (search ?? this.search),
    year: clearYearMonth ? null : (year ?? this.year),
    month: clearYearMonth ? null : (month ?? this.month),
    branch: clearBranch ? null : (branch ?? this.branch),
  );
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

class ExtraProfitListState {
  final List<ExtraProfitModel> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final String? error;
  final ExtraProfitFilter filter;

  const ExtraProfitListState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
    this.filter = const ExtraProfitFilter(),
  });

  ExtraProfitListState copyWith({
    List<ExtraProfitModel>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    String? error,
    ExtraProfitFilter? filter,
    bool clearError = false,
  }) => ExtraProfitListState(
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
// Provider
// ---------------------------------------------------------------------------

final extraProfitsProvider =
    StateNotifierProvider<ExtraProfitsNotifier, ExtraProfitListState>((ref) {
      return ExtraProfitsNotifier(ref.read(extraProfitRepositoryProvider));
    });

class ExtraProfitsNotifier extends StateNotifier<ExtraProfitListState> {
  final ExtraProfitRepository _repo;

  ExtraProfitsNotifier(this._repo) : super(const ExtraProfitListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? ExtraProfitListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final resp = await _repo.getExtraProfits(
        page: refresh ? 1 : state.page,
        search: state.filter.search,
        year: state.filter.year,
        month: state.filter.month,
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
      final resp = await _repo.getExtraProfits(
        page: state.page,
        search: state.filter.search,
        year: state.filter.year,
        month: state.filter.month,
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

  void applyFilter(ExtraProfitFilter filter) {
    state = ExtraProfitListState(filter: filter);
    load();
  }

  Future<String?> createExtraProfit({
    required String amount,
    String? note,
  }) async {
    try {
      await _repo.createExtraProfit(amount: amount, note: note);
      await load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }

  Future<String?> deleteExtraProfit(int id) async {
    try {
      await _repo.deleteExtraProfit(id);
      state = state.copyWith(
        items: state.items.where((e) => e.id != id).toList(),
      );
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

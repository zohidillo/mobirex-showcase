import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_providers.dart';
import '../../data/models/debt_model.dart';
import '../../data/repositories/debt_repository.dart';
import '../../../../shared/utils/error_parser.dart';

final debtRepositoryProvider = Provider<DebtRepository>((ref) {
  return DebtRepository(ref.read(dioClientProvider));
});

// ---------------------------------------------------------------------------
// Filter
// ---------------------------------------------------------------------------

class DebtFilter {
  final String? search;
  final String? direction;
  final int? year;
  final int? month;
  final int? branch;
  final String? domain;

  const DebtFilter({
    this.search,
    this.direction,
    this.year,
    this.month,
    this.branch,
    this.domain,
  });

  DebtFilter copyWith({
    String? search,
    String? direction,
    int? year,
    int? month,
    int? branch,
    String? domain,
    bool clearSearch = false,
    bool clearDirection = false,
    bool clearYearMonth = false,
    bool clearBranch = false,
    bool clearDomain = false,
  }) => DebtFilter(
    search: clearSearch ? null : (search ?? this.search),
    direction: clearDirection ? null : (direction ?? this.direction),
    year: clearYearMonth ? null : (year ?? this.year),
    month: clearYearMonth ? null : (month ?? this.month),
    branch: clearBranch ? null : (branch ?? this.branch),
    domain: clearDomain ? null : (domain ?? this.domain),
  );
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

class DebtListState {
  final List<DebtModel> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final String? error;
  final DebtFilter filter;

  const DebtListState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
    this.filter = const DebtFilter(),
  });

  DebtListState copyWith({
    List<DebtModel>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    String? error,
    DebtFilter? filter,
    bool clearError = false,
  }) => DebtListState(
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
// Unpaid debts
// ---------------------------------------------------------------------------

final unpaidDebtsProvider =
    StateNotifierProvider<UnpaidDebtsNotifier, DebtListState>((ref) {
      return UnpaidDebtsNotifier(ref.read(debtRepositoryProvider), ref);
    });

class UnpaidDebtsNotifier extends StateNotifier<DebtListState> {
  final DebtRepository _repo;
  final Ref _ref;

  UnpaidDebtsNotifier(this._repo, this._ref) : super(const DebtListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? DebtListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final resp = await _repo.getDebts(
        page: refresh ? 1 : state.page,
        search: state.filter.search,
        direction: state.filter.direction,
        year: state.filter.year,
        month: state.filter.month,
        branch: state.filter.branch,
        domain: state.filter.domain,
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
      final resp = await _repo.getDebts(
        page: state.page,
        search: state.filter.search,
        direction: state.filter.direction,
        year: state.filter.year,
        month: state.filter.month,
        branch: state.filter.branch,
        domain: state.filter.domain,
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

  void applyFilter(DebtFilter filter) {
    state = DebtListState(filter: filter);
    load();
  }

  Future<String?> createDebt({
    required String fName,
    required String amount,
    required String direction,
    String? note,
  }) async {
    try {
      final debt = await _repo.createDebt(
        fName: fName,
        amount: amount,
        direction: direction,
        note: note,
      );
      state = state.copyWith(items: [debt, ...state.items]);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }

  Future<String?> payDebt(int id, String amount, {String? note}) async {
    try {
      await _repo.payDebt(id, amount, note: note);
      await load(refresh: true);
      _ref.read(closedDebtsProvider.notifier).load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }

  Future<String?> deleteDebt(int id) async {
    try {
      await _repo.deleteDebt(id);
      state = state.copyWith(
        items: state.items.where((d) => d.id != id).toList(),
      );
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

// ---------------------------------------------------------------------------
// Closed debts
// ---------------------------------------------------------------------------

final closedDebtsProvider =
    StateNotifierProvider<ClosedDebtsNotifier, DebtListState>((ref) {
      return ClosedDebtsNotifier(ref.read(debtRepositoryProvider), ref);
    });

class ClosedDebtsNotifier extends StateNotifier<DebtListState> {
  final DebtRepository _repo;

  ClosedDebtsNotifier(this._repo, Ref _) : super(const DebtListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? DebtListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final resp = await _repo.getClosedDebts(
        page: refresh ? 1 : state.page,
        search: state.filter.search,
        direction: state.filter.direction,
        year: state.filter.year,
        month: state.filter.month,
        branch: state.filter.branch,
        domain: state.filter.domain,
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
      final resp = await _repo.getClosedDebts(
        page: state.page,
        search: state.filter.search,
        direction: state.filter.direction,
        year: state.filter.year,
        month: state.filter.month,
        branch: state.filter.branch,
        domain: state.filter.domain,
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

  void applyFilter(DebtFilter filter) {
    state = DebtListState(filter: filter);
    load();
  }
}

// ---------------------------------------------------------------------------
// Payment history for a specific debt
// ---------------------------------------------------------------------------

class DebtPaymentsState {
  final List<DebtPayment> payments;
  final bool isLoading;
  final String? error;

  const DebtPaymentsState({
    this.payments = const [],
    this.isLoading = true,
    this.error,
  });

  DebtPaymentsState copyWith({
    List<DebtPayment>? payments,
    bool? isLoading,
    String? error,
    bool clearError = false,
  }) => DebtPaymentsState(
    payments: payments ?? this.payments,
    isLoading: isLoading ?? this.isLoading,
    error: clearError ? null : (error ?? this.error),
  );
}

final debtPaymentsProvider =
    StateNotifierProvider.family<DebtPaymentsNotifier, DebtPaymentsState, int>((
      ref,
      debtId,
    ) {
      return DebtPaymentsNotifier(
        ref.read(debtRepositoryProvider),
        ref,
        debtId,
      );
    });

class DebtPaymentsNotifier extends StateNotifier<DebtPaymentsState> {
  final DebtRepository _repo;
  final Ref _ref;
  final int _debtId;
  bool _isFetching = false;

  DebtPaymentsNotifier(this._repo, this._ref, this._debtId)
    : super(const DebtPaymentsState()) {
    load();
  }

  Future<void> load() async {
    if (_isFetching) return;
    _isFetching = true;
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final resp = await _repo.getDebtPayments(debtId: _debtId);
      state = state.copyWith(payments: resp.results, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: parseApiError(e));
    } finally {
      _isFetching = false;
    }
  }

  Future<String?> deletePayment(int paymentId) async {
    try {
      await _repo.deletePayment(paymentId);
      state = state.copyWith(
        payments: state.payments.where((p) => p.id != paymentId).toList(),
      );
      _ref.read(unpaidDebtsProvider.notifier).load(refresh: true);
      _ref.read(closedDebtsProvider.notifier).load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

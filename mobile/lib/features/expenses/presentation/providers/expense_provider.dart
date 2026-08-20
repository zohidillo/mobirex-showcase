import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_providers.dart';
import '../../data/models/expense_model.dart';
import '../../data/repositories/expense_repository.dart';
import '../../../../shared/utils/error_parser.dart';

final expenseRepositoryProvider = Provider<ExpenseRepository>((ref) {
  return ExpenseRepository(ref.read(dioClientProvider));
});

// ---------------------------------------------------------------------------
// Filter
// ---------------------------------------------------------------------------

class ExpenseFilter {
  final String? type;
  final int? year;
  final int? month;
  final int? branch;

  const ExpenseFilter({this.type, this.year, this.month, this.branch});

  ExpenseFilter copyWith({
    String? type,
    int? year,
    int? month,
    int? branch,
    bool clearType = false,
    bool clearYearMonth = false,
    bool clearBranch = false,
  }) => ExpenseFilter(
    type: clearType ? null : (type ?? this.type),
    year: clearYearMonth ? null : (year ?? this.year),
    month: clearYearMonth ? null : (month ?? this.month),
    branch: clearBranch ? null : (branch ?? this.branch),
  );
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

class ExpenseListState {
  final List<ExpenseModel> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final String? error;
  final ExpenseFilter filter;
  final String? totalAmount;

  const ExpenseListState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
    this.filter = const ExpenseFilter(),
    this.totalAmount,
  });

  ExpenseListState copyWith({
    List<ExpenseModel>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    String? error,
    ExpenseFilter? filter,
    String? totalAmount,
    bool clearError = false,
    bool clearTotal = false,
  }) => ExpenseListState(
    items: items ?? this.items,
    isLoading: isLoading ?? this.isLoading,
    isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    hasMore: hasMore ?? this.hasMore,
    page: page ?? this.page,
    error: clearError ? null : (error ?? this.error),
    filter: filter ?? this.filter,
    totalAmount: clearTotal ? null : (totalAmount ?? this.totalAmount),
  );
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

final expensesProvider =
    StateNotifierProvider<ExpensesNotifier, ExpenseListState>((ref) {
      return ExpensesNotifier(ref.read(expenseRepositoryProvider));
    });

class ExpensesNotifier extends StateNotifier<ExpenseListState> {
  final ExpenseRepository _repo;

  ExpensesNotifier(this._repo) : super(const ExpenseListState()) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? ExpenseListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final result = await _repo.getExpenses(
        page: refresh ? 1 : state.page,
        type: state.filter.type,
        year: state.filter.year,
        month: state.filter.month,
        branch: state.filter.branch,
      );
      final resp = result.page;
      state = state.copyWith(
        items: refresh ? resp.results : [...state.items, ...resp.results],
        isLoading: false,
        hasMore: resp.hasMore,
        page: (refresh ? 1 : state.page) + 1,
        totalAmount: result.totalAmount,
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
      final result = await _repo.getExpenses(
        page: state.page,
        type: state.filter.type,
        year: state.filter.year,
        month: state.filter.month,
        branch: state.filter.branch,
      );
      final resp = result.page;
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

  void applyFilter(ExpenseFilter filter) {
    state = ExpenseListState(filter: filter);
    load();
  }

  Future<String?> createExpense({
    required String type,
    required String amount,
    String? note,
  }) async {
    try {
      await _repo.createExpense(type: type, amount: amount, note: note);
      await load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }

  Future<String?> deleteExpense(int id) async {
    try {
      await _repo.deleteExpense(id);
      state = state.copyWith(
        items: state.items.where((e) => e.id != id).toList(),
      );
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

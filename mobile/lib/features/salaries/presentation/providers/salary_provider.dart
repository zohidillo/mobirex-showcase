import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_providers.dart';
import '../../data/models/salary_model.dart';
import '../../data/models/staff_model.dart';
import '../../data/repositories/salary_repository.dart';
import '../../../../shared/utils/error_parser.dart';

final salaryRepositoryProvider = Provider<SalaryRepository>((ref) {
  return SalaryRepository(ref.read(dioClientProvider));
});

final staffListProvider = FutureProvider.family<List<StaffMember>, int?>((
  ref,
  branchId,
) async {
  return ref.read(salaryRepositoryProvider).getStaff(branchId: branchId);
});

// ---------------------------------------------------------------------------
// Filter
// ---------------------------------------------------------------------------

class SalaryFilter {
  final int? year;
  final int? month;
  final int? branch;
  final int? employee;

  const SalaryFilter({this.year, this.month, this.branch, this.employee});

  SalaryFilter copyWith({
    int? year,
    int? month,
    int? branch,
    int? employee,
    bool clearMonth = false,
    bool clearBranch = false,
    bool clearEmployee = false,
  }) => SalaryFilter(
    year: year ?? this.year,
    month: clearMonth ? null : (month ?? this.month),
    branch: clearBranch ? null : (branch ?? this.branch),
    employee: clearEmployee ? null : (employee ?? this.employee),
  );
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

class SalaryListState {
  final List<SalaryModel> items;
  final bool isLoading;
  final bool isLoadingMore;
  final bool hasMore;
  final int page;
  final String? error;
  final SalaryFilter filter;

  const SalaryListState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
    this.filter = const SalaryFilter(),
  });

  SalaryListState copyWith({
    List<SalaryModel>? items,
    bool? isLoading,
    bool? isLoadingMore,
    bool? hasMore,
    int? page,
    String? error,
    SalaryFilter? filter,
    bool clearError = false,
  }) => SalaryListState(
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

final salariesProvider =
    StateNotifierProvider<SalariesNotifier, SalaryListState>((ref) {
      return SalariesNotifier(ref.read(salaryRepositoryProvider));
    });

class SalariesNotifier extends StateNotifier<SalaryListState> {
  final SalaryRepository _repo;

  SalariesNotifier(this._repo)
    : super(SalaryListState(filter: SalaryFilter(year: DateTime.now().year))) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    if (state.isLoading || state.isLoadingMore) return;
    state = refresh
        ? SalaryListState(isLoading: true, filter: state.filter)
        : state.copyWith(isLoading: state.items.isEmpty);
    try {
      final resp = await _repo.getSalaries(
        page: refresh ? 1 : state.page,
        year: state.filter.year,
        month: state.filter.month,
        branch: state.filter.branch,
        employee: state.filter.employee,
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
      final resp = await _repo.getSalaries(
        page: state.page,
        year: state.filter.year,
        month: state.filter.month,
        branch: state.filter.branch,
        employee: state.filter.employee,
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

  void applyFilter(SalaryFilter filter) {
    state = SalaryListState(filter: filter);
    load();
  }

  Future<String?> createSalary({
    required int employeeId,
    required String amount,
    String? note,
  }) async {
    try {
      await _repo.createSalary(
        employeeId: employeeId,
        amount: amount,
        note: note,
      );
      await load(refresh: true);
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }

  Future<String?> deleteSalary(int id) async {
    try {
      await _repo.deleteSalary(id);
      state = state.copyWith(
        items: state.items.where((s) => s.id != id).toList(),
      );
      return null;
    } catch (e) {
      return parseApiError(e);
    }
  }
}

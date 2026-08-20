import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/network/dio_providers.dart';
import '../../../../features/salaries/data/models/staff_model.dart';
import '../../data/models/dashboard_model.dart';
import '../../data/repositories/dashboard_repository.dart';
import '../../../../shared/utils/error_parser.dart';

// ---------------------------------------------------------------------------
// Repository provider
// ---------------------------------------------------------------------------

final dashboardRepositoryProvider = Provider<DashboardRepository>((ref) {
  return DashboardRepository(ref.read(dioClientProvider));
});

// ---------------------------------------------------------------------------
// Staff list for owner flow
// ---------------------------------------------------------------------------

final ownerStaffListProvider = FutureProvider.autoDispose
    .family<List<StaffMember>, int>((ref, branchId) {
      return ref.read(dashboardRepositoryProvider).getStaff(branchId);
    });

// ---------------------------------------------------------------------------
// Dashboard state
// ---------------------------------------------------------------------------

class DashboardState {
  final bool isLoading;
  final String? error;
  final DashboardModel? data;
  final int year;
  final int month;
  final int? branchId;
  final int? staffId;
  final String? role;

  const DashboardState({
    this.isLoading = false,
    this.error,
    this.data,
    required this.year,
    required this.month,
    this.branchId,
    this.staffId,
    this.role,
  });

  DashboardState copyWith({
    bool? isLoading,
    String? error,
    DashboardModel? data,
    int? year,
    int? month,
    int? branchId,
    int? staffId,
    String? role,
    bool clearError = false,
    bool clearData = false,
  }) => DashboardState(
    isLoading: isLoading ?? this.isLoading,
    error: clearError ? null : (error ?? this.error),
    data: clearData ? null : (data ?? this.data),
    year: year ?? this.year,
    month: month ?? this.month,
    branchId: branchId ?? this.branchId,
    staffId: staffId ?? this.staffId,
    role: role ?? this.role,
  );
}

// ---------------------------------------------------------------------------
// Dashboard notifier
// ---------------------------------------------------------------------------

class DashboardNotifier extends StateNotifier<DashboardState> {
  final Ref _ref;

  DashboardNotifier(this._ref)
    : super(
        DashboardState(year: DateTime.now().year, month: DateTime.now().month),
      );

  DashboardRepository get _repo => _ref.read(dashboardRepositoryProvider);

  Future<void> init({
    required int branchId,
    required String role,
    int? staffId,
    int? year,
    int? month,
  }) async {
    final now = DateTime.now();
    state = state.copyWith(
      branchId: branchId,
      staffId: staffId,
      role: role,
      year: year ?? now.year,
      month: month ?? now.month,
      isLoading: true,
      clearError: true,
      clearData: true,
    );
    await _load();
  }

  Future<void> changeFilter(int year, int month) async {
    state = state.copyWith(
      year: year,
      month: month,
      isLoading: true,
      clearError: true,
    );
    await _load();
  }

  Future<void> refresh() async {
    state = state.copyWith(isLoading: true, clearError: true);
    await _load();
  }

  Future<void> _load() async {
    final branchId = state.branchId;
    final role = state.role;
    if (branchId == null || role == null) return;

    try {
      final data = await _repo.getDashboard(
        branchId: branchId,
        role: role,
        staffId: state.staffId,
        year: state.year,
        month: state.month,
      );
      if (mounted) state = state.copyWith(data: data, isLoading: false);
    } catch (e) {
      if (mounted) {
        state = state.copyWith(error: parseApiError(e), isLoading: false);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

final dashboardProvider =
    StateNotifierProvider.autoDispose<DashboardNotifier, DashboardState>((ref) {
      return DashboardNotifier(ref);
    });

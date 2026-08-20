import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/api_constants.dart';
import '../../core/network/dio_client.dart';
import '../../core/network/dio_providers.dart';
import '../models/category_model.dart';
import '../utils/error_parser.dart';

export '../models/category_model.dart';

class CategoryState {
  final List<CategoryItem> categories;
  final bool isLoading;
  final String? error;

  const CategoryState({
    this.categories = const [],
    this.isLoading = false,
    this.error,
  });

  CategoryState copyWith({
    List<CategoryItem>? categories,
    bool? isLoading,
    String? error,
    bool clearError = false,
  }) => CategoryState(
    categories: categories ?? this.categories,
    isLoading: isLoading ?? this.isLoading,
    error: clearError ? null : (error ?? this.error),
  );
}

class CategoryNotifier extends StateNotifier<CategoryState> {
  final DioClient _client;
  final String _endpoint;

  CategoryNotifier(this._client, this._endpoint)
    : super(const CategoryState()) {
    _load();
  }

  Future<void> _load() async {
    if (state.isLoading) return;
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final items = await _fetchAll();
      state = state.copyWith(categories: items, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: parseApiError(e));
    }
  }

  Future<void> reload() => _load();

  Future<List<CategoryItem>> _fetchAll() async {
    final all = <CategoryItem>[];
    int page = 1;
    while (true) {
      final resp = await _client.dio.get(
        _endpoint,
        queryParameters: {'page': page},
      );
      final data = resp.data['data'] as Map<String, dynamic>;
      final results = (data['results'] as List)
          .map((j) => CategoryItem.fromJson(j as Map<String, dynamic>))
          .toList();
      all.addAll(results);
      if (data['next'] == null) break;
      page++;
      if (page > 10) break;
    }
    return all;
  }
}

final phoneCategoriesProvider =
    StateNotifierProvider<CategoryNotifier, CategoryState>((ref) {
      return CategoryNotifier(
        ref.read(dioClientProvider),
        ApiConstants.phoneCategories,
      );
    });

final accessoryCategoriesProvider =
    StateNotifierProvider<CategoryNotifier, CategoryState>((ref) {
      return CategoryNotifier(
        ref.read(dioClientProvider),
        ApiConstants.accessoryCategories,
      );
    });

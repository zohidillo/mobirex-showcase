import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/error_parser.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/empty_state.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../providers/capital_provider.dart';
import '../widgets/capital_card.dart';
import '../widgets/capital_filter_bar.dart';

class AccessoryCapitalPage extends ConsumerStatefulWidget {
  const AccessoryCapitalPage({super.key});

  @override
  ConsumerState<AccessoryCapitalPage> createState() =>
      _AccessoryCapitalPageState();
}

class _AccessoryCapitalPageState extends ConsumerState<AccessoryCapitalPage> {
  final _scrollCtrl = ScrollController();
  bool _showFilters = false;

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollCtrl.position.pixels >=
        _scrollCtrl.position.maxScrollExtent - 200) {
      ref.read(accessoryCapitalProvider.notifier).loadMore();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(accessoryCapitalProvider);
    final user = ref.watch(authProvider).user;

    if (user == null || !user.isOwner) {
      return Scaffold(
        appBar: VelmoraAppBar(subtitle: 'Aksessuar kapitali', showDrawer: true),
        body: const Center(
          child: Text('Sizga bu sahifaga kirish mumkin emas.'),
        ),
      );
    }

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: 'Aksessuar kapitali',
        showDrawer: true,
        actions: [
          AppHeaderButton(
            icon: Icons.tune,
            isActive: _showFilters,
            onPressed: () => setState(() => _showFilters = !_showFilters),
            tooltip: 'Filtr',
          ),
        ],
        bottom: CapitalFilterBar(
          state: state,
          branches: user.branches,
          showFilters: _showFilters,
          onFilterChanged: (f) =>
              ref.read(accessoryCapitalProvider.notifier).applyFilter(f),
        ),
      ),
      body: Column(
        children: [
          CapitalFilterChips(
            state: state,
            branches: user.branches,
            onFilterChanged: (f) =>
                ref.read(accessoryCapitalProvider.notifier).applyFilter(f),
          ),
          const _InfoBanner(),
          Expanded(child: _buildList(state)),
        ],
      ),
    );
  }

  Widget _buildList(CapitalListState state) {
    if (state.isLoading) {
      return ListView.separated(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          AppSpacing.s4,
        ),
        itemCount: 4,
        separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.s3),
        itemBuilder: (_, _) => const AppCardSkeleton(),
      );
    }
    if (state.error != null && state.items.isEmpty) {
      return ErrorView(
        message: parseApiError(state.error),
        onRetry: () =>
            ref.read(accessoryCapitalProvider.notifier).load(refresh: true),
      );
    }
    if (state.items.isEmpty) {
      return EmptyState(
        message: 'Ma\'lumot topilmadi',
        icon: Icons.account_balance_outlined,
        onRefresh: () =>
            ref.read(accessoryCapitalProvider.notifier).load(refresh: true),
      );
    }

    return RefreshIndicator(
      color: AppColors.action,
      backgroundColor: AppColors.card,
      onRefresh: () =>
          ref.read(accessoryCapitalProvider.notifier).load(refresh: true),
      child: ListView.separated(
        controller: _scrollCtrl,
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          AppSpacing.s4,
        ),
        itemCount: state.items.length + (state.isLoadingMore ? 1 : 0),
        separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.s3),
        itemBuilder: (_, i) {
          if (i == state.items.length) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(14),
                child: SizedBox(
                  width: 28,
                  height: 28,
                  child: CircularProgressIndicator(strokeWidth: 3),
                ),
              ),
            );
          }
          return CapitalCard(capital: state.items[i]);
        },
      ),
    );
  }
}

/// Ma'lumot bloki — `.card` uslubidagi yassi izoh qatori.
class _InfoBanner extends StatelessWidget {
  const _InfoBanner();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(AppSpacing.s4, 14, AppSpacing.s4, 0),
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.s4,
        vertical: AppSpacing.s3,
      ),
      decoration: BoxDecoration(
        borderRadius: AppRadius.cardRadius,
        border: Border.all(color: AppColors.line),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline, size: 16, color: AppColors.ink3),
          SizedBox(width: AppSpacing.s2),
          Expanded(
            child: Text(
              'Aksessuar kapitali mahsulot qo\'shish va sotuvlar orqali avtomatik hisoblanadi.',
              style: TextStyle(
                fontSize: 12,
                height: 1.4,
                color: AppColors.ink2,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

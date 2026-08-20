import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/widgets/error_view.dart';
import '../../../../shared/widgets/velmora_app_bar.dart';
import '../../data/models/dashboard_model.dart';
import '../providers/dashboard_provider.dart';
import '../utils/dashboard_utils.dart';
import '../widgets/comparison_section.dart';
import '../widgets/dashboard_filter_bar.dart';
import '../widgets/dashboard_summary_card.dart';
import '../widgets/sales_chart.dart';

class StaffDashboardPage extends ConsumerStatefulWidget {
  final int branchId;
  final int? staffId;
  final String role;
  final String branchName;
  final String? staffName;

  const StaffDashboardPage({
    super.key,
    required this.branchId,
    this.staffId,
    required this.role,
    required this.branchName,
    this.staffName,
  });

  @override
  ConsumerState<StaffDashboardPage> createState() => _StaffDashboardPageState();
}

class _StaffDashboardPageState extends ConsumerState<StaffDashboardPage> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref
          .read(dashboardProvider.notifier)
          .init(
            branchId: widget.branchId,
            role: widget.role,
            staffId: widget.staffId,
          );
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(dashboardProvider);
    final isPhone = widget.role == 'PHONE_SELLER';

    final subtitle = widget.staffName != null
        ? '${widget.staffName} · ${isPhone ? "Telefon" : "Aksessuar"}'
        : isPhone
        ? 'Telefon sotuv'
        : 'Aksessuar sotuv';

    return Scaffold(
      appBar: VelmoraAppBar(
        subtitle: widget.branchName.isNotEmpty
            ? widget.branchName
            : 'Dashboard',
        caption: subtitle,
        actions: [
          // Yuklanayotganda ↻ ko'rsatilmaydi — dizayn 5-ramkasi.
          if (state.data != null)
            AppHeaderButton(
              icon: Icons.refresh,
              tooltip: 'Yangilash',
              onPressed: () => ref.read(dashboardProvider.notifier).refresh(),
            ),
        ],
      ),
      body: _buildBody(context, state),
    );
  }

  Widget _buildBody(BuildContext context, DashboardState state) {
    if (state.isLoading && state.data == null) {
      return const Center(
        child: SizedBox(
          width: 42,
          height: 42,
          child: CircularProgressIndicator(strokeWidth: 3.5),
        ),
      );
    }

    if (state.error != null && state.data == null) {
      return ErrorView(
        message: 'Xato yuz berdi\n${state.error!}',
        onRetry: () => ref.read(dashboardProvider.notifier).refresh(),
      );
    }

    final data = state.data;
    if (data == null) return const SizedBox.shrink();

    return RefreshIndicator(
      onRefresh: () async => ref.read(dashboardProvider.notifier).refresh(),
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.s4,
          14,
          AppSpacing.s4,
          AppSpacing.s6,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DashboardFilterBar(
              selectedYear: state.year,
              selectedMonth: state.month,
              onChanged: (y, m) =>
                  ref.read(dashboardProvider.notifier).changeFilter(y, m),
            ),
            if (data.fromSnapshot || data.snapshotMissing)
              _SnapshotBadge(data),
            const DashboardSectionTitle('Kapital'),
            Row(
              children: [
                Expanded(
                  child: DashboardSummaryCard(
                    label: 'Sarmoya',
                    value: fmtAmount(data.investedAmount),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DashboardSummaryCard(
                    label: 'Joriy balans',
                    value: fmtAmount(data.currentBalance),
                    valueColor: AppColors.pos,
                  ),
                ),
              ],
            ),
            const DashboardSectionTitle('Sotuv va Foyda'),
            if (data.isPhoneDashboard)
              _phoneSalesCards(data)
            else
              _accessorySalesCards(data),
            const DashboardSectionTitle('Qarzlar'),
            _debtCards(data),
            const DashboardSectionTitle('Xarajatlar'),
            _expenseCards(data),
            const DashboardSectionTitle('Inventar'),
            if (data.isPhoneDashboard)
              _phoneInventoryCards(data)
            else
              _accessoryInventoryCards(data),
            const SizedBox(height: AppSpacing.s6),
            ComparisonSection(data: data, role: widget.role),
            const DashboardSectionTitle('Sotuv dinamikasi'),
            SalesChart(series: data.salesSeries),
            if (state.isLoading) ...[
              const SizedBox(height: 16),
              const Center(
                child: SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _phoneSalesCards(DashboardModel data) => Column(
    children: [
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: 'Jami sotuv',
              value: fmtAmount(data.totalSoldValue),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Telefon foyda',
              value: fmtAmount(data.phoneProfit ?? 0),
              valueColor: AppColors.pos,
            ),
          ),
        ],
      ),
      const SizedBox(height: 10),
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: "Qo'shimcha foyda",
              value: fmtAmount(data.extraProfit ?? 0),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Sof foyda',
              value: fmtAmount(data.netProfit ?? 0),
              valueColor: AppColors.pos,
            ),
          ),
        ],
      ),
    ],
  );

  Widget _accessorySalesCards(DashboardModel data) => Column(
    children: [
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: 'Jami sotuv',
              value: fmtAmount(data.totalSoldValue),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Aksessuar foyda',
              value: fmtAmount(data.accessoryProfit ?? 0),
              valueColor: AppColors.pos,
            ),
          ),
        ],
      ),
      const SizedBox(height: 10),
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: 'Sotilgan dona',
              value: '${data.totalQuantitySold ?? 0}',
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Inventar qiymati',
              value: fmtAmount(data.totalInventoryValue ?? 0),
            ),
          ),
        ],
      ),
    ],
  );

  Widget _debtCards(DashboardModel data) => Column(
    children: [
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: "Do'kon qarzdor",
              value: fmtAmount(data.storeOwes),
              valueColor: data.storeOwes > 0 ? AppColors.neg : null,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Boshqalar qarzdor',
              value: fmtAmount(data.othersOwe),
              valueColor: data.othersOwe > 0 ? AppColors.neg : null,
            ),
          ),
        ],
      ),
      const SizedBox(height: 10),
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: "Qarz to'langan",
              value: fmtAmount(data.debtPaid),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Qarz qaytarilgan',
              value: fmtAmount(data.debtReturned),
            ),
          ),
        ],
      ),
    ],
  );

  Widget _expenseCards(DashboardModel data) => Column(
    children: [
      SizedBox(
        width: double.infinity,
        child: DashboardSummaryCard(
          label: 'Jami xarajat',
          value: fmtAmount(data.totalExpense),
        ),
      ),
      const SizedBox(height: 10),
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: "Do'kon xarajati",
              value: fmtAmount(data.shopExpense),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Xodim xarajati',
              value: fmtAmount(data.employeeExpense),
            ),
          ),
        ],
      ),
    ],
  );

  Widget _phoneInventoryCards(DashboardModel data) => Column(
    children: [
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: 'Sotib olingan',
              value: '${data.phonesBoughtCount ?? 0}',
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Sotilgan',
              value: '${data.phonesSoldCount ?? 0}',
            ),
          ),
        ],
      ),
      const SizedBox(height: 10),
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: 'Qolgan',
              value: '${data.phonesRemainingCount ?? 0}',
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Qolgan qiymat',
              value: fmtAmount(data.remainingValue ?? 0),
            ),
          ),
        ],
      ),
      const SizedBox(height: 12),
      SizedBox(
        width: double.infinity,
        child: DashboardSummaryCard(
          label: 'Sotib olish narxi (jami)',
          value: fmtAmount(data.totalCostBought ?? 0),
        ),
      ),
    ],
  );

  Widget _accessoryInventoryCards(DashboardModel data) => Column(
    children: [
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: 'Aksessuar turlari',
              value: '${data.totalAccessoryTypes ?? 0}',
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Jami qoldiq',
              value: '${data.totalStock ?? 0}',
            ),
          ),
        ],
      ),
      const SizedBox(height: 10),
      Row(
        children: [
          Expanded(
            child: DashboardSummaryCard(
              label: 'Qoldiq qiymati',
              value: fmtAmount(data.remainingStockValue ?? 0),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DashboardSummaryCard(
              label: 'Sotilgan dona',
              value: '${data.totalQuantitySold ?? 0}',
            ),
          ),
        ],
      ),
    ],
  );
}

/// `.snap` — 11px `--ink-3`, ikon bilan bitta qator.
class _SnapshotBadge extends StatelessWidget {
  final DashboardModel data;
  const _SnapshotBadge(this.data);

  @override
  Widget build(BuildContext context) {
    final isMissing = data.snapshotMissing;
    final isSnapshot = data.fromSnapshot;
    final color = isMissing ? AppColors.warn : AppColors.ink3;
    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.s3),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isMissing ? Icons.warning_amber_outlined : Icons.schedule,
            size: 14,
            color: color,
          ),
          const SizedBox(width: 6),
          Text(
            isMissing
                ? 'Snapshot topilmadi, live hisoblandi'
                : isSnapshot
                ? 'Snapshotdan olingan'
                : '',
            style: TextStyle(fontSize: 11, color: color),
          ),
        ],
      ),
    );
  }
}

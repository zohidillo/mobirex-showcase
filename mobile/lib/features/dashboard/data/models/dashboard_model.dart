double _d(dynamic v) {
  if (v == null) return 0.0;
  if (v is double) return v;
  if (v is int) return v.toDouble();
  if (v is String) return double.tryParse(v) ?? 0.0;
  return 0.0;
}

class SalesSeriesModel {
  final int day;
  final double amount;

  const SalesSeriesModel({required this.day, required this.amount});

  factory SalesSeriesModel.fromJson(Map<String, dynamic> j) => SalesSeriesModel(
    day: (j['day'] as num?)?.toInt() ?? 0,
    amount: _d(j['amount']),
  );
}

class ComparisonItemModel {
  final double current;
  final double? previous;
  final double? average;
  final double? diff;
  final double? percent;
  final String? direction;

  const ComparisonItemModel({
    required this.current,
    this.previous,
    this.average,
    this.diff,
    this.percent,
    this.direction,
  });

  factory ComparisonItemModel.fromJson(Map<String, dynamic> j) =>
      ComparisonItemModel(
        current: _d(j['current']),
        previous: j['previous'] != null ? _d(j['previous']) : null,
        average: j['average'] != null ? _d(j['average']) : null,
        diff: j['diff'] != null ? _d(j['diff']) : null,
        percent: j['percent'] != null ? (j['percent'] as num).toDouble() : null,
        direction: j['direction'] as String?,
      );
}

class DashboardModel {
  final double investedAmount;
  final double currentBalance;
  final double totalSoldValue;
  final double totalExpense;
  final double shopExpense;
  final double employeeExpense;
  final double storeOwes;
  final double othersOwe;
  final double debtPaid;
  final double debtReturned;
  final List<SalesSeriesModel> salesSeries;

  // Phone-specific
  final double? phoneProfit;
  final double? extraProfit;
  final double? netProfit;
  final int? phonesBoughtCount;
  final int? phonesSoldCount;
  final int? phonesRemainingCount;
  final double? totalCostBought;
  final double? remainingValue;

  // Accessory-specific
  final double? accessoryProfit;
  final int? totalAccessoryTypes;
  final int? totalStock;
  final double? totalInventoryValue;
  final int? totalQuantitySold;
  final double? remainingStockValue;

  // Comparison
  final Map<String, ComparisonItemModel>? previousMonthComparison;
  final Map<String, ComparisonItemModel>? allTimeComparison;

  // Snapshot metadata
  final bool fromSnapshot;
  final String? snapshotMonth;
  final String? snapshotCreatedAt;
  final bool snapshotMissing;

  const DashboardModel({
    required this.investedAmount,
    required this.currentBalance,
    required this.totalSoldValue,
    required this.totalExpense,
    required this.shopExpense,
    required this.employeeExpense,
    required this.storeOwes,
    required this.othersOwe,
    required this.debtPaid,
    required this.debtReturned,
    required this.salesSeries,
    this.phoneProfit,
    this.extraProfit,
    this.netProfit,
    this.phonesBoughtCount,
    this.phonesSoldCount,
    this.phonesRemainingCount,
    this.totalCostBought,
    this.remainingValue,
    this.accessoryProfit,
    this.totalAccessoryTypes,
    this.totalStock,
    this.totalInventoryValue,
    this.totalQuantitySold,
    this.remainingStockValue,
    this.previousMonthComparison,
    this.allTimeComparison,
    this.fromSnapshot = false,
    this.snapshotMonth,
    this.snapshotCreatedAt,
    this.snapshotMissing = false,
  });

  bool get isPhoneDashboard => phoneProfit != null;

  factory DashboardModel.fromJson(Map<String, dynamic> j) {
    Map<String, ComparisonItemModel>? prevMonth;
    Map<String, ComparisonItemModel>? allTime;

    final comp = j['comparison'];
    if (comp is Map<String, dynamic>) {
      final pm = comp['previous_month'];
      if (pm is Map<String, dynamic>) {
        prevMonth = {};
        pm.forEach((k, v) {
          if (v is Map<String, dynamic>) {
            prevMonth![k] = ComparisonItemModel.fromJson(v);
          }
        });
      }
      final at = comp['all_time'];
      if (at is Map<String, dynamic>) {
        allTime = {};
        at.forEach((k, v) {
          if (v is Map<String, dynamic>) {
            allTime![k] = ComparisonItemModel.fromJson(v);
          }
        });
      }
    }

    return DashboardModel(
      investedAmount: _d(j['invested_amount']),
      currentBalance: _d(j['current_balance']),
      totalSoldValue: _d(j['total_sold_value']),
      totalExpense: _d(j['total_expense']),
      shopExpense: _d(j['shop_expense']),
      employeeExpense: _d(j['employee_expense']),
      storeOwes: _d(j['store_owes']),
      othersOwe: _d(j['others_owe']),
      debtPaid: _d(j['debt_paid']),
      debtReturned: _d(j['debt_returned']),
      salesSeries:
          (j['sales_series'] as List<dynamic>?)
              ?.map((e) => SalesSeriesModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      phoneProfit: j.containsKey('phone_profit') ? _d(j['phone_profit']) : null,
      extraProfit: j.containsKey('extra_profit') ? _d(j['extra_profit']) : null,
      netProfit: j.containsKey('net_profit') ? _d(j['net_profit']) : null,
      phonesBoughtCount: (j['phones_bought_count'] as num?)?.toInt(),
      phonesSoldCount: (j['phones_sold_count'] as num?)?.toInt(),
      phonesRemainingCount: (j['phones_remaining_count'] as num?)?.toInt(),
      totalCostBought: j.containsKey('total_cost_bought')
          ? _d(j['total_cost_bought'])
          : null,
      remainingValue: j.containsKey('remaining_value')
          ? _d(j['remaining_value'])
          : null,
      accessoryProfit: j.containsKey('accessory_profit')
          ? _d(j['accessory_profit'])
          : null,
      totalAccessoryTypes: (j['total_accessory_types'] as num?)?.toInt(),
      totalStock: (j['total_stock'] as num?)?.toInt(),
      totalInventoryValue: j.containsKey('total_inventory_value')
          ? _d(j['total_inventory_value'])
          : null,
      totalQuantitySold: (j['total_quantity_sold'] as num?)?.toInt(),
      remainingStockValue: j.containsKey('remaining_stock_value')
          ? _d(j['remaining_stock_value'])
          : null,
      previousMonthComparison: prevMonth,
      allTimeComparison: allTime,
      fromSnapshot: j['from_snapshot'] as bool? ?? false,
      snapshotMonth: j['snapshot_month'] as String?,
      snapshotCreatedAt: j['snapshot_created_at'] as String?,
      snapshotMissing: j['snapshot_missing'] as bool? ?? false,
    );
  }
}

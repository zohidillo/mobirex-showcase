class CapitalBranch {
  final int id;
  final String name;
  final String address;
  final bool isActive;

  const CapitalBranch({
    required this.id,
    required this.name,
    required this.address,
    required this.isActive,
  });

  factory CapitalBranch.fromJson(Map<String, dynamic> j) => CapitalBranch(
    id: j['id'] as int,
    name: j['name'] as String? ?? '',
    address: j['address'] as String? ?? '',
    isActive: j['is_active'] as bool? ?? true,
  );
}

class CapitalModel {
  /// Backend joriy oy uchun HALI YOZUV YO'Q bo'lsa `is_placeholder: true` va
  /// `id: null` bilan qator qaytaradi — bu normal holat, xato emas.
  /// Shuning uchun `int?`. Soxta `0` qo'yilmaydi: u keyinroq haqiqiy
  /// yozuv bilan chalkashtirib yuborardi.
  final int? id;
  final CapitalBranch? branch;
  final int? branchId;
  final DateTime? month;
  final double investedAmount;
  final double currentBalance;
  final DateTime? addedAt;
  final DateTime? updatedAt;

  const CapitalModel({
    this.id,
    this.branch,
    this.branchId,
    this.month,
    required this.investedAmount,
    required this.currentBalance,
    this.addedAt,
    this.updatedAt,
  });

  factory CapitalModel.fromJson(Map<String, dynamic> j) => CapitalModel(
    id: j['id'] as int?,
    branch: _parseBranch(j['branch']),
    branchId: j['branch_id'] as int?,
    month: _parseDate(j['month']),
    investedAmount: _parseDouble(j['invested_amount']),
    currentBalance: _parseDouble(j['current_balance']),
    addedAt: _parseDate(j['added_at']),
    updatedAt: _parseDate(j['updated_at']),
  );

  bool get isCurrentMonth {
    if (month == null) return false;
    final now = DateTime.now();
    return month!.year == now.year && month!.month == now.month;
  }
}

/// Filial obyekti yo'q, `null`, yoki `id` siz kelsa — `null` qaytaradi.
///
/// [CapitalBranch.id] ataylab `int` bo'lib qoladi: u ilovada filtr uchun
/// haqiqatan o'qiladi, shuning uchun soxta `0` xavfli bo'lardi. Noto'liq
/// filial "filial yo'q" deb qaraladi — model allaqachon `branch: null` ni
/// qo'llab-quvvatlaydi.
CapitalBranch? _parseBranch(dynamic v) {
  if (v is! Map<String, dynamic>) return null;
  if (v['id'] is! int) return null;
  return CapitalBranch.fromJson(v);
}

double _parseDouble(dynamic v) {
  if (v == null) return 0.0;
  if (v is num) return v.toDouble();
  if (v is String) return double.tryParse(v) ?? 0.0;
  return 0.0;
}

DateTime? _parseDate(dynamic v) {
  if (v == null) return null;
  if (v is String && v.isNotEmpty) {
    try {
      return DateTime.parse(v);
    } catch (_) {
      return null;
    }
  }
  return null;
}

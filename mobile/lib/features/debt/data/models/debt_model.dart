class DebtBranch {
  final int id;
  final String name;

  const DebtBranch({required this.id, required this.name});

  factory DebtBranch.fromJson(Map<String, dynamic> json) =>
      DebtBranch(id: json['id'] as int, name: json['name'] as String? ?? '');
}

class DebtUser {
  final int id;
  final String username;

  const DebtUser({required this.id, required this.username});

  factory DebtUser.fromJson(Map<String, dynamic> json) => DebtUser(
    id: json['id'] as int,
    username: json['username'] as String? ?? '',
  );
}

class DebtPayment {
  final int id;
  final int debtId;
  final String amount;
  final String? note;
  final DebtUser? paidBy;
  final String addedAt;

  const DebtPayment({
    required this.id,
    required this.debtId,
    required this.amount,
    this.note,
    this.paidBy,
    required this.addedAt,
  });

  factory DebtPayment.fromJson(Map<String, dynamic> json) => DebtPayment(
    id: json['id'] as int,
    debtId: json['debt_id'] as int? ?? 0,
    amount: json['amount'] as String? ?? '0.00',
    note: json['note'] as String?,
    paidBy: json['paid_by'] != null
        ? DebtUser.fromJson(json['paid_by'] as Map<String, dynamic>)
        : null,
    addedAt: json['added_at'] as String? ?? '',
  );
}

class DebtModel {
  final int id;
  final String fName;
  final String amount;
  final String remainingAmount;
  final String direction;
  final String directionDisplay;
  final String? note;
  final DebtBranch? branch;
  final int branchId;
  final DebtUser? createdBy;
  final int createdById;
  final List<DebtPayment> payments;
  final String addedAt;
  final String updatedAt;

  const DebtModel({
    required this.id,
    required this.fName,
    required this.amount,
    required this.remainingAmount,
    required this.direction,
    required this.directionDisplay,
    this.note,
    this.branch,
    required this.branchId,
    this.createdBy,
    required this.createdById,
    required this.payments,
    required this.addedAt,
    required this.updatedAt,
  });

  bool get isWeGave => direction == 'WE_GAVE';

  factory DebtModel.fromJson(Map<String, dynamic> json) => DebtModel(
    id: json['id'] as int,
    fName: json['f_name'] as String? ?? '',
    amount: json['amount'] as String? ?? '0.00',
    remainingAmount: json['remaining_amount'] as String? ?? '0.00',
    direction: json['direction'] as String? ?? '',
    directionDisplay: json['direction_display'] as String? ?? '',
    note: json['note'] as String?,
    branch: json['branch'] != null
        ? DebtBranch.fromJson(json['branch'] as Map<String, dynamic>)
        : null,
    branchId: json['branch_id'] as int? ?? 0,
    createdBy: json['created_by'] != null
        ? DebtUser.fromJson(json['created_by'] as Map<String, dynamic>)
        : null,
    createdById: json['created_by_id'] as int? ?? 0,
    payments:
        (json['payments'] as List<dynamic>?)
            ?.map((e) => DebtPayment.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [],
    addedAt: json['added_at'] as String? ?? '',
    updatedAt: json['updated_at'] as String? ?? '',
  );
}

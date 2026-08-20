class ExpenseBranch {
  final int id;
  final String name;
  const ExpenseBranch({required this.id, required this.name});
  factory ExpenseBranch.fromJson(Map<String, dynamic> j) =>
      ExpenseBranch(id: j['id'] as int, name: j['name'] as String? ?? '');
}

class ExpenseUser {
  final int id;
  final String username;
  const ExpenseUser({required this.id, required this.username});
  factory ExpenseUser.fromJson(Map<String, dynamic> j) =>
      ExpenseUser(id: j['id'] as int, username: j['username'] as String? ?? '');
}

class ExpenseModel {
  final int id;
  final String type;
  final String typeDisplay;
  final String amount;
  final String? note;
  final ExpenseBranch? branch;
  final ExpenseUser? createdBy;
  final ExpenseUser? employee;
  final String addedAt;

  const ExpenseModel({
    required this.id,
    required this.type,
    required this.typeDisplay,
    required this.amount,
    this.note,
    this.branch,
    this.createdBy,
    this.employee,
    required this.addedAt,
  });

  factory ExpenseModel.fromJson(Map<String, dynamic> j) => ExpenseModel(
    id: j['id'] as int,
    type: j['type'] as String? ?? '',
    typeDisplay: j['type_display'] as String? ?? j['type'] as String? ?? '',
    amount: j['amount'] as String? ?? '0.00',
    note: (j['note'] as String?)?.isNotEmpty == true
        ? j['note'] as String
        : null,
    branch: j['branch'] != null
        ? ExpenseBranch.fromJson(j['branch'] as Map<String, dynamic>)
        : null,
    createdBy: j['created_by'] != null
        ? ExpenseUser.fromJson(j['created_by'] as Map<String, dynamic>)
        : null,
    employee: j['employee'] != null
        ? ExpenseUser.fromJson(j['employee'] as Map<String, dynamic>)
        : null,
    addedAt: j['added_at'] as String? ?? '',
  );
}

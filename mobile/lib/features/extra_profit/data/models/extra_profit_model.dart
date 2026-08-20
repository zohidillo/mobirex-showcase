class ExtraProfitBranch {
  final int id;
  final String name;
  const ExtraProfitBranch({required this.id, required this.name});
  factory ExtraProfitBranch.fromJson(Map<String, dynamic> j) =>
      ExtraProfitBranch(id: j['id'] as int, name: j['name'] as String? ?? '');
}

class ExtraProfitUser {
  final int id;
  final String username;
  const ExtraProfitUser({required this.id, required this.username});
  factory ExtraProfitUser.fromJson(Map<String, dynamic> j) => ExtraProfitUser(
    id: j['id'] as int,
    username: j['username'] as String? ?? '',
  );
}

class ExtraProfitModel {
  final int id;
  final String amount;
  final String? note;
  final ExtraProfitBranch? branch;
  final ExtraProfitUser? createdBy;
  final String addedAt;

  const ExtraProfitModel({
    required this.id,
    required this.amount,
    this.note,
    this.branch,
    this.createdBy,
    required this.addedAt,
  });

  factory ExtraProfitModel.fromJson(Map<String, dynamic> j) => ExtraProfitModel(
    id: j['id'] as int,
    amount: j['amount'] as String? ?? '0.00',
    note: (j['note'] as String?)?.isNotEmpty == true
        ? j['note'] as String
        : null,
    branch: j['branch'] != null
        ? ExtraProfitBranch.fromJson(j['branch'] as Map<String, dynamic>)
        : null,
    createdBy: j['created_by'] != null
        ? ExtraProfitUser.fromJson(j['created_by'] as Map<String, dynamic>)
        : null,
    addedAt: j['added_at'] as String? ?? '',
  );
}

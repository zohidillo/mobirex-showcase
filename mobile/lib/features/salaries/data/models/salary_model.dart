class SalaryEmployee {
  final int id;
  final String username;
  final String firstName;
  final String lastName;

  const SalaryEmployee({
    required this.id,
    required this.username,
    required this.firstName,
    required this.lastName,
  });

  String get fullName => '$firstName $lastName'.trim();
  String get displayName => fullName.isNotEmpty ? fullName : username;

  factory SalaryEmployee.fromJson(Map<String, dynamic> j) => SalaryEmployee(
    id: j['id'] as int,
    username: j['username'] as String? ?? '',
    firstName: j['first_name'] as String? ?? '',
    lastName: j['last_name'] as String? ?? '',
  );
}

class SalaryBranch {
  final int id;
  final String name;
  const SalaryBranch({required this.id, required this.name});
  factory SalaryBranch.fromJson(Map<String, dynamic> j) =>
      SalaryBranch(id: j['id'] as int, name: j['name'] as String? ?? '');
}

class SalaryCreator {
  final int id;
  final String username;
  const SalaryCreator({required this.id, required this.username});
  factory SalaryCreator.fromJson(Map<String, dynamic> j) => SalaryCreator(
    id: j['id'] as int,
    username: j['username'] as String? ?? '',
  );
}

class SalaryModel {
  final int id;
  final SalaryEmployee? employee;
  final SalaryBranch? branch;
  final String amount;
  final String? note;
  final SalaryCreator? createdBy;
  final String addedAt;

  const SalaryModel({
    required this.id,
    this.employee,
    this.branch,
    required this.amount,
    this.note,
    this.createdBy,
    required this.addedAt,
  });

  factory SalaryModel.fromJson(Map<String, dynamic> j) => SalaryModel(
    id: j['id'] as int,
    employee: j['employee'] != null
        ? SalaryEmployee.fromJson(j['employee'] as Map<String, dynamic>)
        : null,
    branch: j['branch'] != null
        ? SalaryBranch.fromJson(j['branch'] as Map<String, dynamic>)
        : null,
    amount: j['amount'] as String? ?? '0.00',
    note: (j['note'] as String?)?.isNotEmpty == true
        ? j['note'] as String
        : null,
    createdBy: j['created_by'] != null
        ? SalaryCreator.fromJson(j['created_by'] as Map<String, dynamic>)
        : null,
    addedAt: j['added_at'] as String? ?? '',
  );
}

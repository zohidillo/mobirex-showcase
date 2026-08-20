class StaffMember {
  final int id;
  final String username;
  final String firstName;
  final String lastName;
  final String role;
  final int? branchId;
  final String? branchName;

  const StaffMember({
    required this.id,
    required this.username,
    required this.firstName,
    required this.lastName,
    required this.role,
    this.branchId,
    this.branchName,
  });

  String get fullName => '$firstName $lastName'.trim();
  String get displayName => fullName.isNotEmpty ? fullName : username;

  factory StaffMember.fromJson(Map<String, dynamic> j) => StaffMember(
    id: j['user_id'] as int,
    username: j['username'] as String? ?? '',
    firstName: j['first_name'] as String? ?? '',
    lastName: j['last_name'] as String? ?? '',
    role: j['role'] as String? ?? '',
    branchId: j['branch_id'] as int?,
    branchName: j['branch_name'] as String?,
  );
}

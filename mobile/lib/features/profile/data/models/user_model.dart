import '../../../../core/constants/billing_status.dart';

/// Real-time billing state for the signed-in user, mirrored from `/api/me/`'s
/// `billing` object. The backend computes this from `evaluate_user()`, so it is
/// the source of truth for the UI — prefer it over the raw `accountStatus`.
///
/// Fully null-safe: VIP/active users get empty messages and a null
/// `graceDaysLeft`, and an older build (or a response missing `billing`) parses
/// into a benign active-like state instead of throwing.
class BillingStatus {
  /// One of [BillingStatuses] (active / grace / blocked / vip).
  final String status;
  final bool isBlocked;
  final bool isGrace;
  final String warningMessage;
  final String blockedMessage;
  final String? graceStartDate;
  final int? graceDaysLeft;

  const BillingStatus({
    required this.status,
    required this.isBlocked,
    required this.isGrace,
    required this.warningMessage,
    required this.blockedMessage,
    required this.graceStartDate,
    required this.graceDaysLeft,
  });

  /// A safe default used when the server omits `billing` (e.g. old backend).
  /// Treated as active so nothing is blocked or warned on unknown state.
  const BillingStatus.unknown()
    : status = BillingStatuses.active,
      isBlocked = false,
      isGrace = false,
      warningMessage = '',
      blockedMessage = '',
      graceStartDate = null,
      graceDaysLeft = null;

  factory BillingStatus.fromJson(Map<String, dynamic> json) => BillingStatus(
    status: json['status'] as String? ?? BillingStatuses.active,
    isBlocked: json['is_blocked'] as bool? ?? false,
    isGrace: json['is_grace'] as bool? ?? false,
    warningMessage: json['warning_message'] as String? ?? '',
    blockedMessage: json['blocked_message'] as String? ?? '',
    graceStartDate: json['grace_start_date'] as String?,
    graceDaysLeft: json['grace_days_left'] as int?,
  );

  bool get isVip => status == BillingStatuses.vip;
  bool get isActive => status == BillingStatuses.active;
}

class UserRole {
  final int branchId;
  final String branchName;
  final String role;

  const UserRole({
    required this.branchId,
    required this.branchName,
    required this.role,
  });

  factory UserRole.fromJson(Map<String, dynamic> json) => UserRole(
    branchId: json['branch_id'] as int,
    branchName: json['branch_name'] as String,
    role: json['role'] as String,
  );
}

class UserBranch {
  final int id;
  final String name;
  final String role;

  const UserBranch({required this.id, required this.name, required this.role});

  factory UserBranch.fromJson(Map<String, dynamic> json) => UserBranch(
    id: json['id'] as int,
    name: json['name'] as String,
    role: json['role'] as String? ?? '',
  );
}

class UserModel {
  final int id;
  final String username;
  final String firstName;
  final String lastName;
  final String fullName;
  final String phone;
  final String accountStatus;
  final String accountStatusDisplay;
  final String balance;
  final bool isVip;
  final BillingStatus billing;
  final bool isSuperuser;
  final bool isCashier;
  final String theme;
  final bool hasPin;
  final bool pinEnabled;
  final List<UserRole> roles;
  final List<UserBranch> branches;

  const UserModel({
    required this.id,
    required this.username,
    required this.firstName,
    required this.lastName,
    required this.fullName,
    required this.phone,
    required this.accountStatus,
    required this.accountStatusDisplay,
    required this.balance,
    required this.isVip,
    required this.billing,
    required this.isSuperuser,
    required this.isCashier,
    required this.theme,
    required this.hasPin,
    required this.pinEnabled,
    required this.roles,
    required this.branches,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
    id: json['id'] as int,
    username: json['username'] as String,
    firstName: json['first_name'] as String? ?? '',
    lastName: json['last_name'] as String? ?? '',
    fullName: json['full_name'] as String? ?? '',
    phone: json['phone'] as String? ?? '',
    accountStatus: json['account_status'] as String? ?? '',
    accountStatusDisplay: json['account_status_display'] as String? ?? '',
    balance: _balanceToString(json['balance']),
    isVip: json['is_vip'] as bool? ?? false,
    billing: json['billing'] is Map<String, dynamic>
        ? BillingStatus.fromJson(json['billing'] as Map<String, dynamic>)
        : const BillingStatus.unknown(),
    isSuperuser: json['is_superuser'] as bool? ?? false,
    isCashier: json['is_cashier'] as bool? ?? false,
    theme: json['theme'] as String? ?? 'system',
    hasPin: json['has_pin'] as bool? ?? false,
    pinEnabled: json['pin_enabled'] as bool? ?? false,
    roles:
        (json['roles'] as List<dynamic>?)
            ?.map((e) => UserRole.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [],
    branches:
        (json['branches'] as List<dynamic>?)
            ?.map((e) => UserBranch.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [],
  );

  UserModel copyWith({
    bool? hasPin,
    bool? pinEnabled,
    String? theme,
    String? username,
  }) => UserModel(
    id: id,
    username: username ?? this.username,
    firstName: firstName,
    lastName: lastName,
    fullName: fullName,
    phone: phone,
    accountStatus: accountStatus,
    accountStatusDisplay: accountStatusDisplay,
    balance: balance,
    isVip: isVip,
    billing: billing,
    isSuperuser: isSuperuser,
    isCashier: isCashier,
    theme: theme ?? this.theme,
    hasPin: hasPin ?? this.hasPin,
    pinEnabled: pinEnabled ?? this.pinEnabled,
    roles: roles,
    branches: branches,
  );

  /// Backend returns `balance` as a decimal string (e.g. "-9900.00"); tolerate
  /// a numeric value too so an older/newer serializer shape never crashes.
  static String _balanceToString(dynamic value) {
    if (value == null) return '';
    if (value is String) return value;
    return value.toString();
  }

  /// Demo accounts used for App Store review. The backend blocks credential
  /// and account changes for these users, so the app disables those actions
  /// up front instead of surfacing a raw server error.
  static const Set<String> _demoUsernames = {
    'demo_owner',
    'demo_phone',
    'demo_accessory',
  };

  bool get isDemo => _demoUsernames.contains(username.toLowerCase());

  bool get isOwner => roles.any((r) => r.role == 'OWNER');
  bool get isPhoneSeller => roles.any((r) => r.role == 'PHONE_SELLER');
  bool get isAccessorySeller => roles.any((r) => r.role == 'ACCESSORY_SELLER');
  bool get isSeller => isPhoneSeller || isAccessorySeller;
  bool get hasMultipleBranches => branches.length > 1;

  // --- Billing (display layer) — always derived from `billing`, never from
  // the raw `accountStatus` field. VIP is exempt from every warning/block. ---

  /// Show the amber grace banner: in grace and not a VIP/demo account.
  bool get showGraceBanner => billing.isGrace && !billing.isVip;

  /// The account is blocked and business endpoints will return 402.
  bool get isBillingBlocked => billing.isBlocked && !billing.isVip;
}

/// Billing/account lifecycle states as computed by the backend
/// (`GraceStatusService`) and returned in `/api/me/` under `billing.status`.
///
/// These lowercase strings must match the backend EXACTLY. The mobile UI must
/// always rely on `billing.status` (real-time, from `evaluate_user`) and never
/// on the raw `account_status` DB field, which can lag behind on mobile because
/// the web middleware does not persist it for JWT requests.
class BillingStatuses {
  const BillingStatuses._();

  /// Account in good standing — no warnings, full access.
  static const String active = 'active';

  /// Balance depleted; a short grace window is running before the block.
  static const String grace = 'grace';

  /// Grace window elapsed; business endpoints return 402.
  static const String blocked = 'blocked';

  /// Exempt account (demo / VIP) — never warned, never blocked.
  static const String vip = 'vip';
}

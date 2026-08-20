class ApiConstants {
  static const String baseUrl = String.fromEnvironment(
    'BASE_URL',
    defaultValue: 'https://api.mobirex.uz',
    // defaultValue: 'http://192.168.0.163:8080',
  );

  // Auth
  static const String login = '/api/auth/login/';
  static const String refresh = '/api/auth/refresh/';
  static const String changePassword = '/api/auth/change-password/';
  static const String accountDelete = '/api/account/delete/';

  // PIN
  static const String pinSet = '/api/auth/pin/set/';
  static const String pinVerify = '/api/auth/pin/verify/';
  static const String pinChange = '/api/auth/pin/change/';

  // Current user
  static const String me = '/api/me/';
  static const String meSettings = '/api/me/settings/';
  static const String ownerBranches = '/api/me/branches/';
  static const String ownerStaff = '/api/me/staff/';

  // Phones
  static const String phonesUnsold = '/api/phones/unsold/';
  static const String phonesSold = '/api/phones/sold/';
  static const String phones = '/api/phones/';
  static String phoneDetail(int id) => '/api/phones/$id/';
  static String phoneSell(int id) => '/api/phones/$id/sell/';
  static String phoneReturn(int id) => '/api/phones/$id/return/';

  // Accessories
  static const String accessoriesUnsold = '/api/accessories/unsold/';
  static const String accessoriesSold = '/api/accessories/sold/';
  static const String accessories = '/api/accessories/';
  static String accessoryDetail(int id) => '/api/accessories/$id/';
  static String accessorySell(int id) => '/api/accessories/$id/sell/';
  static String accessoryReturn(int saleId) =>
      '/api/accessories/sales/$saleId/return/';

  // Debts
  static const String debts = '/api/debts/';
  static const String closedDebts = '/api/debts/closed/';
  static const String debtPayments = '/api/debts/payments/';
  static String debtDetail(int id) => '/api/debts/$id/';
  static String debtPay(int id) => '/api/debts/$id/pay/';
  static String debtPaymentDetail(int id) => '/api/debts/payments/$id/';

  // Expenses
  static const String expenses = '/api/expenses/';
  static String expenseDetail(int id) => '/api/expenses/$id/';

  // Salaries
  static const String salaries = '/api/salary/';
  static String salaryDetail(int id) => '/api/salary/$id/';

  // Extra Profits
  static const String extraProfits = '/api/extra-profit/';
  static String extraProfitDetail(int id) => '/api/extra-profit/$id/';

  // Capital
  static const String phoneCapital = '/api/capital/phone/';
  static const String phoneCapitalReset = '/api/capital/phone/reset/';
  static const String accessoryCapital = '/api/capital/accessory/';

  // Categories
  static const String phoneCategories = '/api/categories/phone/';
  static const String accessoryCategories = '/api/categories/accessory/';

  // Dashboard
  static const String dashboardStaff = '/api/dashboard/staff/';

  // Public (autentifikatsiyasiz — login ekranidan bog'lanish so'rovi)
  static const String publicContactRequest = '/api/public/contact-request/';
  static const String regions = '/api/regions/';

  // Support
  static const String supportRequests = '/api/support/requests/';
  static String supportRequestDetail(int id) => '/api/support/requests/$id/';
  static String supportRequestMessages(int id) =>
      '/api/support/requests/$id/messages/';

  // Error Reporting
  static const String errorReport = '/api/error-report/';
}

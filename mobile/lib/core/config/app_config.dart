// Production URL is injected at build time:
//   flutter build apk --release --dart-define=BASE_URL=https://crm.b26.uz
// The defaultValue below is used when no dart-define is passed (debug/local runs).
const String baseUrl = String.fromEnvironment(
  'BASE_URL',
  defaultValue: 'https://api.mobirex.uz',
  // defaultValue: 'http://192.168.0.163:8080',
);

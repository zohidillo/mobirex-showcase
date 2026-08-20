# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app (with configurable backend URL)
flutter run --dart-define=BASE_URL=http://192.168.0.164:8888

# Build APK
flutter build apk --dart-define=BASE_URL=http://192.168.0.164:8888

# Install dependencies
flutter pub get

# Analyze code
flutter analyze

# Run all tests
flutter test

# Run a single test file
flutter test test/widget_test.dart
```

## Architecture

Feature-based structure under `lib/`:

```
core/
  config/       # baseUrl via dart-define
  constants/    # token keys, page size
  network/      # DioClient + AuthInterceptor (QueuedInterceptorsWrapper)
  router/       # GoRouter + RouterNotifier (ChangeNotifier bridging Riverpod → GoRouter)
  storage/      # SecureStorageService (flutter_secure_storage)
  theme/        # AppTheme (dark/light/system) + themeProvider

features/
  auth/         # login, PIN set/verify/change, auth state machine
  profile/      # /api/me/ user model, settings, password change
  phones/       # unsold + sold lists, add/sell/return/delete
  accessories/  # unsold + sold lists, add/sell/return/delete

shared/
  widgets/      # AppShell (drawer), PinInputWidget, AppButton, EmptyState, ErrorView
  utils/        # DateFormatter, ErrorParser
```

Each feature follows the pattern: `data/models/` → `data/repositories/` → `presentation/providers/` → `presentation/pages/` → `presentation/widgets/`.

## Key Architectural Decisions

**Auth state machine** (`authProvider` is a `StateNotifierProvider<AuthNotifier, AuthState>`):
- `AuthStatus.loading` → startup, checking tokens
- `AuthStatus.unauthenticated` → no valid tokens → redirect `/login`
- `AuthStatus.pinRequired` → tokens valid, user loaded, `has_pin=true` → redirect `/pin/verify`
- `AuthStatus.authenticated` → fully ready → redirect to `/phones/unsold`

**Startup flow** (as per API contract):
1. Check secure storage for tokens
2. No token → unauthenticated
3. Token exists → call `/api/me/`
4. `/api/me/` 401 → try refresh via interceptor
5. Refresh fails → clear storage → unauthenticated
6. `/api/me/` success → apply theme, check `has_pin`
7. `has_pin=true` → `pinRequired` state
8. After PIN verify → `authenticated`

**Token refresh** — handled in `AuthInterceptor` (extends `QueuedInterceptorsWrapper`). Uses a separate internal Dio instance for refresh calls to avoid recursion. On refresh failure, sets `sessionExpiredNotifier.value = true` (a global `ValueNotifier<bool>`). `AuthNotifier` listens to this and transitions to `unauthenticated`.

**GoRouter refresh** — `RouterNotifier extends ChangeNotifier` reads `authProvider` via Riverpod `Ref` and calls `notifyListeners()` on state changes. GoRouter uses this as `refreshListenable`.

**Paginated lists** — Both phone and accessory lists use `StateNotifier<PaginatedListState<T>>`. Filters (search, category, branch, year/month) are held in the state; changing any filter resets to page 1 and reloads. `load(refresh: true)` resets the list; `loadMore()` appends next page.

**API response envelope** — All paginated responses are wrapped: `{ success, data: { count, next, previous, results } }`. Repositories unwrap `data.results` / `data.count` / `data.next`.

**Theme** — Backend `/api/me/` returns `theme: "system"|"light"|"dark"`. `themeProvider` derives `ThemeMode` from auth state. `SharedPreferences` caches the theme for fast startup before `/api/me/` returns.

**Categories in forms** — There is no `/api/categories/` endpoint in the contract. Form dropdowns derive unique categories from already-loaded list data (exposed via provider getters).

**Branches in forms** — User's branches come from `/api/me/` (`user.branches`). Branch dropdown uses this list; branch filter shown only when user has multiple branches or is an owner.

## API Contract Source of Truth

`docs/mobile_api_contract.md` — do not deviate from response shapes documented there. Key rules:
- Login response contains only `access` and `refresh` — call `/api/me/` immediately after.
- PIN is 4 digits, stored hashed on backend, never returned.
- Sold phones/accessories default to current month; use `year`/`month` params for past months.
- Return is only allowed for current-month sales.
- Sold phones cannot be deleted directly (return first).
- Accessory with active sales cannot be deleted.

## Modules Not Yet Implemented

Per the contract: Debt, Expense, Salary, Extra Profit, Dashboard. Do not add these until their API sections are documented.

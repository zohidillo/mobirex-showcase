# Velmora Mobile API Contract

````markdown

This document describes the API contract for the **Velmora Flutter mobile app**.

## Important Rules

- Flutter must use this document as the source of truth for API integration.
- Do not guess endpoint response shapes.
- Login and refresh use SimpleJWT default response.
- Profile, roles, branches, theme, and PIN status come from `/api/me/`.
- Phone and accessory business logic must match the backend/web behavior.
- For now, show both **Phone** and **Accessory** sections in the app sidebar for all authenticated users.
- Role-based menu hiding will be added later.
- Do not implement Debt yet. Debt API documentation will be added later.

---

# 1. Base URL

The Flutter app must use a configurable base URL.

Example:

```dart
const baseUrl = String.fromEnvironment(
  'BASE_URL',
  defaultValue: 'http://192.168.0.164:8888',
);
````

Run example:

```bash
flutter run --dart-define=BASE_URL=http://192.168.0.164:8888
```

All endpoints below are relative to `baseUrl`.

---

# 2. Authentication

## 2.1 Login

### Endpoint

```http
POST /api/auth/login/
```

### Request

```json
{
  "username": "akmal97",
  "password": "123"
}
```

### Response

```json
{
  "refresh": "refresh-token-here",
  "access": "access-token-here"
}
```

### Rules

* Do not expect user data in the login response.
* Save access and refresh tokens securely.
* After login, call `/api/me/` to get:

  * current user profile
  * roles
  * branches
  * theme
  * PIN status

---

## 2.2 Refresh Access Token

### Endpoint

```http
POST /api/auth/refresh/
```

### Request

```json
{
  "refresh": "refresh-token-here"
}
```

### Response

```json
{
  "access": "new-access-token-here"
}
```

### Rules

* Use the refresh token until it expires.
* If refresh fails, logout and return to the login page.

---

# 3. Current User Profile

## 3.1 Get Current User

### Endpoint

```http
GET /api/me/
```

### Headers

```http
Authorization: Bearer <access_token>
```

### Response Example

```json
{
  "id": 1,
  "username": "owner_api",
  "first_name": "Mobile",
  "last_name": "Owner",
  "full_name": "Mobile Owner",
  "phone": "+998900001122",
  "account_status": "active",
  "is_superuser": false,
  "is_cashier": false,
  "theme": "light",
  "has_pin": true,
  "pin_enabled": true,
  "roles": [
    {
      "branch_id": 1,
      "branch_name": "Main Branch",
      "role": "OWNER"
    }
  ],
  "branches": [
    {
      "id": 1,
      "name": "Main Branch",
      "role": "OWNER"
    }
  ]
}
```

### Flutter Usage

* Use `roles` and `branches` to understand user context.
* Use `theme` to restore app theme.
* Use `has_pin` or `pin_enabled` to decide whether to show:

  * PIN setup page
  * PIN verify page

---

# 4. User Settings

## 4.1 Update Current User Settings

### Endpoint

```http
PATCH /api/me/settings/
```

### Headers

```http
Authorization: Bearer <access_token>
```

### Request Examples

Update theme:

```json
{
  "theme": "dark"
}
```

Update username:

```json
{
  "username": "new_username"
}
```

### Possible Theme Values

```text
system
light
dark
```

### Response

Backend returns updated user/settings data.

After successful update, Flutter should either:

* refresh `/api/me/`
* or update local state from the response

### Rules

* User can update only own settings.
* Username must be unique.
* Do not allow updating another user.

---

## 4.2 Change Password

### Endpoint

```http
POST /api/auth/change-password/
```

### Headers

```http
Authorization: Bearer <access_token>
```

### Request Example

```json
{
  "old_password": "old-password",
  "new_password": "new-password",
  "new_password_confirm": "new-password"
}
```

### Rules

* Old password is required.
* New password must be saved using backend password hashing.
* Flutter must not store password.

---

# 5. PIN Code

PIN is for mobile app security/unlock flow.

## Important

* PIN is exactly 4 digits.
* PIN is stored hashed on the backend.
* PIN hash is never returned to Flutter.
* PIN does not replace JWT authentication.
* All PIN endpoints require access token.

---

## 5.1 Set PIN

### Endpoint

```http
POST /api/auth/pin/set/
```

### Headers

```http
Authorization: Bearer <access_token>
```

### Request

```json
{
  "pin": "1234"
}
```

### Success Response Example

```json
{
  "success": true,
  "has_pin": true,
  "pin_enabled": true
}
```

### Validation

* PIN must be exactly 4 digits.
* Reject non-digit PIN.
* Reject length not equal to 4.

---

## 5.2 Verify PIN

### Endpoint

```http
POST /api/auth/pin/verify/
```

### Headers

```http
Authorization: Bearer <access_token>
```

### Request

```json
{
  "pin": "1234"
}
```

### Success Response Example

```json
{
  "success": true
}
```

### Failure

* Wrong PIN returns an error.
* If no PIN is set, backend returns a clear error.

### Flutter Usage

* When app opens and token exists, ask PIN if `has_pin=true`.
* PIN verify unlocks local app UI.
* It does not issue a new JWT token.

---

## 5.3 Change PIN

### Endpoint

```http
POST /api/auth/pin/change/
```

### Headers

```http
Authorization: Bearer <access_token>
```

### Request

```json
{
  "old_pin": "1234",
  "new_pin": "5678"
}
```

### Success Response Example

```json
{
  "success": true,
  "has_pin": true,
  "pin_enabled": true
}
```

### Rules

* Old PIN must match.
* New PIN must be exactly 4 digits.

---

# 6. Pagination Format

All paginated list APIs should use this response format:

```json
{
  "success": true,
  "data": {
    "count": 100,
    "next": "https://example.com/api/phones/unsold/?page=2",
    "previous": null,
    "results": []
  }
}
```

## Rules

* Default page size: `20`.
* Items are inside `data.results`.
* Total item count is `data.count`.
* Use `data.next` and `data.previous` for pagination.

## Flutter Parser Should Expect

```
response.data["data"]["results"];
response.data["data"]["count"];
response.data["data"]["next"];
response.data["data"]["previous"];
```

---

# 7. Phone API

## Phone Endpoints

```http
GET    /api/phones/unsold/
GET    /api/phones/sold/
POST   /api/phones/
DELETE /api/phones/<id>/
POST   /api/phones/<id>/sell/
POST   /api/phones/<id>/return/
```

## Business Rules

* Unsold phones remain visible across months.
* Sold phones appear only in the month where they were sold.
* Sold list defaults to current month.
* Past sold phones are visible using year/month filter.
* Return is allowed only for current-month sold phones.
* Past-month sold phones can be viewed but not returned.
* Sold phones cannot be deleted directly.
* User must return sold phone first, then delete if needed.
* Adding phone subtracts `cost_price` from `PhoneCapital.current_balance`.
* Selling phone adds `sell_price` to `PhoneCapital.current_balance`.
* Returning sold phone subtracts `sell_price` from `PhoneCapital.current_balance`.
* Deleting unsold phone restores `cost_price` to `PhoneCapital.current_balance`.
* `PhoneCapital.invested_amount` must not change from add/sell/return/delete.
* Phone actions must affect only the phone’s own branch capital.

---

## 7.1 Unsold Phone List

### Endpoint

```http
GET /api/phones/unsold/
```

### Query Params

```text
page
q
name
imei
category
storage
branch   # owner only
```

### Examples

```http
GET /api/phones/unsold/
GET /api/phones/unsold/?q=iphone
GET /api/phones/unsold/?imei=123456
GET /api/phones/unsold/?category=1
GET /api/phones/unsold/?storage=128
GET /api/phones/unsold/?branch=2
```

### Response Example

```json
{
  "success": true,
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 10,
        "name": "iPhone 13",
        "imei": "123456789",
        "storage": "128",
        "color": "Black",
        "cost_price": "400.00",
        "sell_price": null,
        "is_sold": false,
        "category": {
          "id": 1,
          "name": "Smartphones"
        },
        "branch": {
          "id": 1,
          "name": "Main Branch"
        }
      }
    ]
  }
}
```

### Note

Serializer fields may differ slightly. Flutter must map available fields safely.

---

## 7.2 Sold Phone List

### Endpoint

```http
GET /api/phones/sold/
```

### Default

Returns current-month sold phones.

### Query Params

```text
page
q
name
imei
category
storage
year
month
branch   # owner only
```

### Examples

```http
GET /api/phones/sold/
GET /api/phones/sold/?year=2026&month=3
GET /api/phones/sold/?q=iphone
GET /api/phones/sold/?branch=2&year=2026&month=4
```

### Response Example

```json
{
  "success": true,
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 15,
        "name": "iPhone 13",
        "imei": "123456789",
        "storage": "128",
        "color": "Black",
        "cost_price": "400.00",
        "sell_price": "500.00",
        "is_sold": true,
        "sold_at": "2026-04-20T10:00:00+05:00",
        "category": {
          "id": 1,
          "name": "Smartphones"
        },
        "branch": {
          "id": 1,
          "name": "Main Branch"
        }
      }
    ]
  }
}
```

---

## 7.3 Create Phone

### Endpoint

```http
POST /api/phones/
```

### Request Example

```json
{
  "name": "iPhone 13",
  "category": 1,
  "branch": 1,
  "imei": "123456789",
  "storage": "128",
  "color": "Black",
  "from_by": "Supplier",
  "cost_price": "400.00"
}
```

### Rules

* Owner can create in owned branches.
* Phone seller can create in own branch.
* Accessory seller must be blocked.
* On success, `cost_price` is subtracted from `PhoneCapital.current_balance`.

### Response Example

```json
{
  "success": true,
  "data": {
    "id": 10,
    "name": "iPhone 13",
    "imei": "123456789"
  }
}
```

---

## 7.4 Sell Phone

### Endpoint

```http
POST /api/phones/<id>/sell/
```

### Request

```json
{
  "sell_price": "500.00"
}
```

### Rules

* Only unsold phone can be sold.
* Owner can sell in owned branches.
* Phone seller can sell in own branch.
* Same-branch phone sellers can sell peer-added phones.
* Accessory seller is blocked.
* On success, `sell_price` is added to `PhoneCapital.current_balance`.

### Response Example

```json
{
  "success": true,
  "data": {
    "id": 10,
    "is_sold": true,
    "sell_price": "500.00"
  }
}
```

---

## 7.5 Return Sold Phone

### Endpoint

```http
POST /api/phones/<id>/return/
```

### Request

```json
{}
```

### Rules

* Only current-month sold phones can be returned.
* Past-month sold phones cannot be returned.
* On success, `sell_price` is subtracted from `PhoneCapital.current_balance`.
* Phone becomes unsold again.

### Response Example

```json
{
  "success": true,
  "data": {
    "id": 10,
    "is_sold": false
  }
}
```

---

## 7.6 Delete Phone

### Endpoint

```http
DELETE /api/phones/<id>/
```

### Rules

* Sold phones cannot be deleted.
* User must return sold phone first.
* Only unsold phones can be deleted.
* On delete, `cost_price` is added back to `PhoneCapital.current_balance`.
* Delete must affect only the phone’s branch capital.

### Response Example

```json
{
  "success": true,
  "message": "Deleted successfully"
}
```

---

# 8. Accessory API

## Accessory Endpoints

```http
GET    /api/accessories/unsold/
GET    /api/accessories/sold/
GET    /api/accessories/employees/
POST   /api/accessories/
POST   /api/accessories/<id>/sell/
POST   /api/accessories/sales/<id>/return/
DELETE /api/accessories/<id>/
```

## Business Rules

* Accessories with stock remain visible across months.
* Sold accessory sales appear only in the month where `sold_at` belongs.
* Sold list defaults to current month.
* Past sales are visible with year/month filter.
* Return is allowed only for current-month sales.
* Past-month sales cannot be returned.
* Product with active sales cannot be deleted.
* If 10 items were added and 3 sold, delete is blocked until those 3 sales are returned.
* Returning a sale for a deleted accessory is blocked.
* Adding accessory increases `AccessoryCapital.invested_amount`.
* Selling accessory increases `AccessoryCapital.current_balance`.
* Returning accessory sale subtracts `total_price` from `AccessoryCapital.current_balance` and restores stock.
* Deleting accessory rolls back `AccessoryCapital.invested_amount` only when delete is valid.
* Accessory actions must never affect `PhoneCapital`.
* Accessory actions must affect only the accessory’s own branch capital.

---

## 8.1 Unsold / In-Stock Accessory List

### Endpoint

```http
GET /api/accessories/unsold/
```

### Query Params

```text
page
q
name
category
branch   # owner only
employee # if API supports it
```

### Examples

```http
GET /api/accessories/unsold/
GET /api/accessories/unsold/?q=charger
GET /api/accessories/unsold/?category=3
GET /api/accessories/unsold/?branch=2
```

### Response Example

```json
{
  "success": true,
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 5,
        "name": "60W Charger",
        "category": {
          "id": 3,
          "name": "Chargers"
        },
        "branch": {
          "id": 1,
          "name": "Main Branch"
        },
        "unit_cost": "20.00",
        "stock": 10,
        "image": "https://example.com/media/accessories/charger.jpg"
      }
    ]
  }
}
```

---

## 8.2 Sold Accessory List

### Endpoint

```http
GET /api/accessories/sold/
```

### Default

Returns current-month sold accessory sales.

### Query Params

```text
page
q
name
category
year
month
branch   # owner only
employee # if API supports it
```

### Examples

```http
GET /api/accessories/sold/
GET /api/accessories/sold/?year=2026&month=3
GET /api/accessories/sold/?q=charger
GET /api/accessories/sold/?branch=2&year=2026&month=4
```

### Response Example

```json
{
  "success": true,
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 20,
        "accessory": {
          "id": 5,
          "name": "60W Charger",
          "image": "https://example.com/media/accessories/charger.jpg"
        },
        "branch": {
          "id": 1,
          "name": "Main Branch"
        },
        "quantity": 3,
        "unit_cost": "20.00",
        "total_cost": "60.00",
        "total_price": "90.00",
        "profit": "30.00",
        "sold_at": "2026-04-20T10:00:00+05:00"
      }
    ]
  }
}
```

---

## 8.3 Create Accessory

### Endpoint

```http
POST /api/accessories/
```

### Request Example

```json
{
  "name": "60W Charger",
  "category": 3,
  "branch": 1,
  "unit_cost": "20.00",
  "stock": 10,
  "image": "<multipart-file-if-supported>"
}
```

### Rules

* Owner can create in owned branches.
* Accessory seller can create in own branch.
* Phone seller is blocked.
* On success:

  * `AccessoryCapital.invested_amount += stock * unit_cost`
  * `PhoneCapital` must not change.

### File Upload

If image upload is used, request should be:

```http
multipart/form-data
```

### Response Example

```json
{
  "success": true,
  "data": {
    "id": 5,
    "name": "60W Charger",
    "stock": 10
  }
}
```

---

## 8.4 Sell Accessory

### Endpoint

```http
POST /api/accessories/<id>/sell/
```

### Request

```json
{
  "quantity": 3,
  "total_price": "90.00"
}
```

### Rules

* Quantity must be available in stock.
* Owner can sell in owned branches.
* Accessory seller can sell in own branch.
* Same-branch accessory sellers can sell peer-added products.
* Phone seller is blocked.
* On success:

  * stock decreases by quantity
  * `AccessoryCapital.current_balance += total_price`
  * `PhoneCapital` must not change

### Response Example

```json
{
  "success": true,
  "data": {
    "id": 20,
    "accessory": 5,
    "quantity": 3,
    "total_price": "90.00",
    "profit": "30.00"
  }
}
```

---

## 8.5 Return Accessory Sale

### Endpoint

```http
POST /api/accessories/sales/<sale_id>/return/
```

### Request

```json
{}
```

### Rules

* Only current-month sale can be returned.
* Past-month sale cannot be returned.
* Return for deleted accessory is blocked.
* On success:

  * stock increases by returned quantity
  * `AccessoryCapital.current_balance -= total_price`
  * sale becomes deleted/returned according to backend design
  * `PhoneCapital` must not change

### Response Example

```json
{
  "success": true,
  "data": {
    "id": 20,
    "returned": true
  }
}
```

---

## 8.6 Delete Accessory

### Endpoint

```http
DELETE /api/accessories/<id>/
```

### Rules

* Product with active sales cannot be deleted.
* Example: added 10, sold 3, remaining 7 — delete is blocked.
* First return all active sales.
* After all active sales are returned, delete is allowed if permission rules allow it.
* On valid delete:

  * `AccessoryCapital.invested_amount` rolls back by `stock * unit_cost`
  * `AccessoryCapital.current_balance` must not change
  * `PhoneCapital` must not change

### Response Example

```json
{
  "success": true,
  "message": "Deleted successfully"
}
```

---

# 9. Flutter App Pages For First Version

For now implement these pages only.

## 9.1 Auth

* Login page
* PIN setup page
* PIN verify page
* PIN change page

## 9.2 Profile / Settings

* Profile page
* Update username
* Change password
* Theme selection:

  * system
  * light
  * dark

## 9.3 Phone

* Unsold phone list
* Sold phone list
* Add phone
* Sell phone
* Return sold phone
* Delete unsold phone

### Phone Filters

* Search by name/IMEI
* Category
* Storage
* Year/month for sold list
* Branch for owner

## 9.4 Accessory

* Unsold accessory list
* Sold accessory list
* Add accessory
* Sell accessory
* Return sale
* Delete accessory

### Accessory Filters

* Search by name
* Category
* Year/month for sold list
* Branch for owner
* Show image if available

## 9.5 Sidebar

For now:

* Show Phone menu.
* Show Accessory menu.
* Show Settings/Profile menu.
* Do not hide menus by role yet.
* Later role-based menu visibility will be added.

---

# 10. Flutter Implementation Notes

Use:

* Dio for HTTP.
* Flutter Secure Storage for access/refresh tokens.
* Riverpod for state management.
* GoRouter for navigation.
* SharedPreferences only for lightweight local cache like theme fallback.
* Server `/api/me/` is the source of truth for theme and profile.

---

## 10.1 Recommended App Startup Flow

```text
1. Check secure storage for tokens.
2. If no token -> LoginPage.
3. If token exists -> call /api/me/.
4. If /api/me/ fails with expired access -> refresh token.
5. If refresh succeeds -> retry /api/me/.
6. If refresh fails -> clear tokens and go LoginPage.
7. If /api/me/ succeeds:
   - apply theme
   - check has_pin
   - if has_pin=true -> PinVerifyPage
   - if has_pin=false -> optional PinSetPage or HomePage depending UX
8. After PIN success -> Home/AppShell.
```

---

# 11. Not Included Yet

Do not implement these modules yet:

* Debt module
* Expense module
* Salary module
* Extra profit module
* Dashboard module

These will be documented and added later.

```
```

---

# 12. UI / UX Design Guidelines

The Flutter app name is **Velmora**.

## 12.1 General Style

- The app should look clean, modern, and minimal.
- Use a dark-first design, but support system/light/dark themes.
- Use rounded cards, soft shadows, and comfortable spacing.
- Avoid crowded screens.
- Keep forms simple and readable.
- Main actions should be easy to find.

## 12.2 Theme

Supported themes:

- `system`
- `light`
- `dark`

Theme source of truth:

- Backend `/api/me/` returns the saved theme.
- User can update theme from Settings.
- Flutter should cache theme locally only for fast startup.
- Backend theme should remain the final source of truth.

## 12.3 Navigation

Use an AppShell layout with:

- AppBar
- Sidebar / Drawer
- Main content area

For now sidebar must show:

- Phones
- Accessories
- Profile / Settings
- Logout

Do not hide sidebar items by role yet. Role-based menu visibility will be added later.

## 12.4 Auth Screens

### Login Page

Login page should include:

- Velmora app name
- Username input
- Password input
- Login button
- Loading state
- Error message area

Do not show user profile data on login response. After successful login, call `/api/me/`.

### PIN Setup Page

PIN setup page should include:

- 4-digit PIN input
- Confirm PIN input if needed
- Save button
- Validation for exactly 4 digits

### PIN Verify Page

PIN verify page should include:

- 4-digit PIN input
- Clear error on wrong PIN
- Logout/change account option

### PIN Change Page

PIN change page should include:

- Old PIN input
- New PIN input
- Save button

## 12.5 List Pages

Phone and accessory list pages should have:

- Search field at the top
- Filter button or filter section
- List cards
- Pull-to-refresh
- Infinite scroll or next-page loading
- Empty state
- Error state
- Loading state

Each card should show the most important data first.

## 12.6 Phone UI

### Unsold Phones

Each unsold phone card should show:

- Name
- IMEI
- Category
- Storage
- Color
- Cost price
- Branch name if available
- Action buttons:
  - Sell
  - Delete

### Sold Phones

Each sold phone card should show:

- Name
- IMEI
- Category
- Storage
- Sell price
- Sold date
- Branch name if available
- Action buttons:
  - Return only if current-month sale is returnable

Past-month sold phones should be view-only.

## 12.7 Accessory UI

### Unsold / In-stock Accessories

Each accessory card should show:

- Image if available
- Name
- Category
- Stock
- Unit cost
- Branch name if available
- Action buttons:
  - Sell
  - Delete

If the product has active sales, delete may fail. Show backend error clearly.

### Sold Accessories

Each sold accessory card should show:

- Image if available
- Product name
- Quantity
- Total price
- Profit
- Sold date
- Branch name if available
- Action buttons:
  - Return only if current-month sale is returnable

Past-month sold accessories should be view-only.

## 12.8 Forms

Forms should be simple.

Use:

- Text fields for name, IMEI, storage, color, prices
- Dropdowns for category and branch
- Number input for quantity and prices
- Image picker for accessory image if API supports multipart upload

All submit buttons should have loading state and disabled state.

## 12.9 Filters

Filters should be easy to open/close.

Phone filters:

- Search by name/IMEI
- Category
- Storage
- Year/month for sold list
- Branch for owner

Accessory filters:

- Search by name
- Category
- Year/month for sold list
- Branch for owner

For now, show branch filter only if user has multiple branches or owner role information from `/api/me/`.

## 12.10 Error Handling

Show backend validation errors clearly.

Examples:

- Sold phone cannot be deleted.
- Past-month sale cannot be returned.
- Accessory with active sales cannot be deleted.
- Wrong PIN.
- Token expired.
- Permission denied.

Do not show raw stack traces or technical errors to the user.

## 12.11 Loading and Empty States

Every list page must have:

- Loading spinner/skeleton
- Empty state message
- Retry button on error

Examples:

- “No phones found”
- “No accessories found”
- “No sold products this month”

## 12.12 Colors

Use a professional dark theme.

Suggested style:

- Primary color: dark orange / amber
- Background: dark navy or near black
- Cards: slightly lighter dark surface
- Text: high contrast
- Error: red
- Success: green

Do not hardcode colors everywhere. Use centralized theme files.

## 12.13 Code Organization

Flutter code should follow feature-based structure:

```text
lib/
  main.dart
  app.dart

  core/
    config/
    constants/
    network/
    router/
    theme/
    storage/

  features/
    auth/
    profile/
    phones/
    accessories/

  shared/
    widgets/
    utils/
```
12.14 First Version Scope

Implement only:

Auth
/api/me/
PIN set/verify/change
Theme/settings
Phones
Accessories

# Debt API

## Business Rules

- Owner can view, pay, and delete debts in owned branches.
- Owner cannot create debts.
- Sellers can create debts only in their own branch.
- Phone seller creates and sees only `PHONE` debts.
- Accessory seller creates and sees only `ACCESSORY` debts.
- Phone seller cannot see/access accessory debts.
- Accessory seller cannot see/access phone debts.
- Same branch + same domain sellers can see and pay each other’s debts.
- Seller can delete only current-month debts they created.
- Owner can delete any current-month debt in owned branches.
- Past-month debt payment is blocked.
- Past-month debt delete is blocked.
- Default debt list shows current-month unpaid debts.
- Closed debt list shows fully paid debts.
- Past debts are visible using year/month filter.
- Search by `f_name` is supported.
- Direction filter supports `WE_GAVE` and `WE_TOOK`.
- Owner can filter by branch.

## Capital Rules

### WE_TOOK — Biz oldik

- Create debt: current balance increases.
- Pay debt: current balance decreases.
- Delete debt: remaining amount decreases from current balance.

### WE_GAVE — Biz berdik

- Create debt: current balance decreases.
- Pay debt: current balance increases.
- Delete debt: remaining amount returns to current balance.

Phone debt affects only `PhoneCapital`.
Accessory debt affects only `AccessoryCapital`.

---

## Endpoints

```http
GET    /api/debts/
POST   /api/debts/
GET    /api/debts/closed/
POST   /api/debts/<id>/pay/
DELETE /api/debts/<id>/
GET    /api/debts/payments/
DELETE /api/debts/payments/<id>/
List Unpaid Debts
GET /api/debts/
```
Default:

Returns current-month unpaid debts only.

Query params:

page
q
type       # WE_GAVE or WE_TOOK
year
month
branch     # owner only
created_by # owner only
domain     # owner only, PHONE or ACCESSORY
history_mode # selected or full

Example:
```
GET /api/debts/?q=Ali&type=WE_GAVE
GET /api/debts/?year=2026&month=3
GET /api/debts/?branch=2
```
Response:
```
{
  "success": true,
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "f_name": "Ali",
        "amount": "100.00",
        "remaining_amount": "70.00",
        "direction": "WE_GAVE",
        "direction_display": "Biz berdik",
        "note": "Test debt",
        "branch": {
          "id": 1,
          "name": "Main Branch",
          "address": "",
          "is_active": true
        },
        "branch_id": 1,
        "created_by": {
          "id": 5,
          "username": "seller1"
        },
        "created_by_id": 5,
        "payments": [],
        "added_at": "2026-04-29T10:00:00+05:00",
        "updated_at": "2026-04-29T10:00:00+05:00"
      }
    ]
  }
}
List Closed / Fully Paid Debts
GET /api/debts/closed/
```
Default:

Returns current-month fully paid debts.

Query params:

page
q
type
year
month
branch
created_by
domain
history_mode

Response shape is the same as /api/debts/, plus closed_at.

Create Debt
POST /api/debts/

Request:
```
{
  "f_name": "Ali",
  "amount": "100.00",
  "direction": "WE_GAVE",
  "note": "Optional note"
}
```
Rules:

Only sellers can create debt.
Owner cannot create debt.
Branch is automatically taken from seller profile.
Domain is automatically assigned:
phone seller -> PHONE
accessory seller -> ACCESSORY

Response:
```
{
  "success": true,
  "data": {
    "id": 1,
    "f_name": "Ali",
    "amount": "100.00",
    "remaining_amount": "100.00",
    "direction": "WE_GAVE"
  }
}
Pay Debt
POST /api/debts/<id>/pay/
```
Request:
```
{
  "amount": "30.00",
  "note": "Partial payment"
}
```
Rules:

Payment amount cannot exceed remaining_amount.
Owner can pay debts in owned branches.
Seller can pay same branch + same domain debts.
Past-month debt payment is blocked.

Response:
```
{
  "success": true,
  "data": {
    "id": 10,
    "debt_id": 1,
    "amount": "30.00",
    "remaining_balance": "70.00",
    "debt_remaining_amount": "70.00",
    "paid_by": {
      "id": 5,
      "username": "seller1"
    },
    "paid_by_id": 5,
    "note": "Partial payment",
    "added_at": "2026-04-29T10:00:00+05:00",
    "updated_at": "2026-04-29T10:00:00+05:00"
  }
}
Delete Debt
DELETE /api/debts/<id>/
```
Rules:

Owner can delete current-month debts in owned branches.
Seller can delete only current-month debts they created.
Past-month debt delete is blocked.

Response:
```
{
  "success": true,
  "data": {
    "message": "Qarz o‘chirildi."
  }
}
List Debt Payments
GET /api/debts/payments/
```
Default:

Returns payments for current-month debts.

Query params:

page
year
month

Response:
```
{
  "success": true,
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 10,
        "debt_id": 1,
        "amount": "30.00",
        "remaining_balance": "70.00",
        "debt_remaining_amount": "70.00",
        "paid_by": {
          "id": 5,
          "username": "seller1"
        },
        "paid_by_id": 5,
        "note": "Partial payment",
        "added_at": "2026-04-29T10:00:00+05:00",
        "updated_at": "2026-04-29T10:00:00+05:00"
      }
    ]
  }
}
Delete Debt Payment
DELETE /api/debts/payments/<id>/
```
Rules:

Payment delete is owner-only.
Seller cannot delete payments.
Past-month payment delete is blocked.
Delete recalculates debt remaining amount and reverses capital safely.

Response:
```
{
  "success": true,
  "data": {
    "message": "To‘lov o‘chirildi."
  }
}```

Fix ONLY these Flutter UI/navigation/settings bugs. Do not touch backend code. Do not change API contracts. Do not implement new modules.

Project context:
- Flutter app is Velmora.
- API contract is documented in docs/mobile_api_contract.md.
- Current scope: auth, /me, PIN, settings/theme, phones, accessories, debt.
- Keep existing architecture, Dio/Riverpod/GoRouter structure, and current UI style.

Bugs to fix:

1. Sidebar/drawer does not close after navigating
Problem:
- When the sidebar/drawer is opened and user taps a menu item, the app navigates to another page but the sidebar stays open.
- It closes only after tapping an empty area.
Expected:
- When any sidebar menu item is tapped, close the drawer first, then navigate to the selected page.
- This must work for all sidebar items: phones, accessories, debt, settings/profile, logout if applicable.
Implementation hint:
- Before navigation, call Navigator.of(context).pop() if the drawer is open.
- Then run GoRouter navigation.
- Avoid double-pop bugs.
- Do not break back navigation.

2. PIN setup button opens a blank page
Problem:
- When user taps “PIN code setup” / “Pin kod qo‘yish”, it navigates to an empty page.
Expected:
- It should open the real PIN setup page.
- If PIN is already set, it should open PIN change page or show correct settings action according to existing UX.
- The route must be correctly registered in GoRouter.
- The button must use the correct route name/path.
- The page must render input fields and submit button.

Check:
- Pin setup page widget exists.
- Pin change page widget exists.
- Settings/profile button points to correct route.
- Route path/name is not mismatched.
- No placeholder/empty Scaffold is being opened.

3. Change password confirm password validation is broken
Problem:
- In change password form, even when confirm password is filled, app still says confirm password was not entered.
Expected:
- Confirm password field value must be correctly read from controller/form state.
- Validation should check:
  - old password is not empty
  - new password is not empty
  - confirm password is not empty
  - new password == confirm password
- Payload sent to backend must match docs/mobile_api_contract.md:
  {
    "old_password": "...",
    "new_password": "...",
    "new_password_confirm": "..."
  }
- If backend currently expects a different key, inspect the existing API call and align with the documented backend contract.
- Do not send empty confirm password.
- Show backend validation errors clearly.

Required checks:
- Search all settings/profile/PIN/password routes and widgets.
- Fix route names/paths if mismatched.
- Fix controllers or form keys if confirm password uses the wrong controller.
- Make sure all TextEditingControllers are disposed if StatefulWidget is used.
- Keep UI clean and consistent.

Tests / validation:
- Run flutter analyze.
- If widget tests exist, run them.
- Manually verify from code flow:
  1. Open drawer -> tap Phones -> drawer closes and page changes.
  2. Open drawer -> tap Accessories -> drawer closes and page changes.
  3. Open drawer -> tap Debt -> drawer closes and page changes if debt menu exists.
  4. Settings -> PIN setup opens real PIN setup page.
  5. Settings -> Change password accepts confirm password and sends new_password_confirm.

After implementation, report:
- changed files
- exact drawer fix
- exact PIN route fix
- exact password confirm fix
- commands run and results
- any remaining issue

Important:
Do not touch backend.
Do not change unrelated Flutter screens.
Do not implement expense/salary/extra-profit/dashboard.

For this task, work autonomously and finish the implementation without asking me step-by-step questions.

You may read, edit, create, and update files inside this project.
You may run safe commands such as:
- grep/find/ls/cat
- flutter analyze
- dart format
- flutter test if tests exist

Do not ask confirmation for normal code edits, route fixes, formatting, or analysis commands.
Only stop and ask me if:
- a command can delete data/files
- a command can reset git history
- a command can modify backend/database/migrations
- the requested behavior is impossible without changing backend API

Do not touch backend code.
Do not change API contracts.
Do not implement unrelated modules.

Complete the Flutter bugfix task fully, then report:
- changed files
- what was fixed
- commands run
- remaining issues if any
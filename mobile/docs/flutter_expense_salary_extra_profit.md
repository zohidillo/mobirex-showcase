# Velmora Flutter — Expense, Salary, Extra Profit Implementation Guide

This document is the source of truth for implementing the next Flutter modules:

- Expense
- Salary
- Extra Profit

The backend APIs and business logic must be followed exactly. Do not guess behavior. If API response fields are slightly different, map safely but keep the same business behavior.

---

# 1. General Flutter Rules

## 1.1 Scope

Implement only these modules:

- Expense
- Salary
- Extra Profit

Do not implement or modify:

- Dashboard
- Month close
- Auth
- PIN
- Phone business logic
- Accessory business logic
- Debt business logic
- Backend code

Small shared UI improvements are allowed only if they help keep all list pages consistent.

---

## 1.2 Navigation / Sidebar

Add these sidebar navigation items:

- Expenses
- Salaries
- Extra Profit

Sidebar should include existing modules too:

- Phones
- Accessories
- Debts
- Expenses
- Salaries
- Extra Profit
- Profile / Settings
- Logout

When user taps any sidebar item:

1. Close the drawer/sidebar.
2. Navigate to the selected page.

Do not leave the drawer open after navigation.

---

## 1.3 Floating Add Button Rule

All list modules must use the same add button pattern.

Use one consistent FloatingActionButton position:

```text
Bottom right corner
```

This applies to:

- Phone add
- Accessory add
- Debt add
- Expense add
- Salary add
- Extra Profit add

If some older pages use different add button positions, align them to the same bottom-right FloatingActionButton style when safe.

Rules:

- Add button should be visible only if the user is allowed to create that object.
- Owner cannot create Expense.
- Owner can create Salary.
- Owner cannot create Extra Profit.
- Seller can create Expense.
- Phone seller can create Extra Profit.
- Accessory seller cannot create Extra Profit.
- Seller cannot create Salary.

---

## 1.4 List Page Standards

Every list page must have:

- Clean app bar/title
- Search/filter area when needed
- List cards
- Loading state
- Empty state
- Error state
- Pull-to-refresh
- Pagination / infinite scroll if API is paginated
- FloatingActionButton for create action if user has permission

Every create/delete action must refresh the relevant list after success.

---

## 1.5 Standard Paginated Response

All list APIs use this structure:

```json
{
  "success": true,
  "data": {
    "count": 100,
    "next": "https://example.com/api/example/?page=2",
    "previous": null,
    "results": []
  }
}
```

Flutter must parse:

```dart
final results = response.data["data"]["results"];
final count = response.data["data"]["count"];
final next = response.data["data"]["next"];
final previous = response.data["data"]["previous"];
```

Default page size is 20.

---

# 2. Owner Helper APIs

These APIs are used for filters and forms.

## 2.1 Owner Branches

Endpoint:

```http
GET /api/me/branches/
```

Purpose:

- Returns branches owned by the current owner.
- Used in branch filters.
- Used in Salary create form.
- Used in Owner views for Expense, Salary, and Extra Profit.

Auth:

```http
Authorization: Bearer <access_token>
```

Expected response example:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Main Branch",
      "address": "Optional address",
      "is_active": true
    }
  ]
}
```

Flutter usage:

- Load once after `/api/me/` for owner users.
- Use in branch dropdown filters.
- If current user is not owner, this API may return 403 or empty data. Handle safely.

---

## 2.2 Owner Staff

Endpoint:

```http
GET /api/me/staff/
```

Optional branch filter:

```http
GET /api/me/staff/?branch=1
```

Purpose:

- Returns sellers in branches owned by current owner.
- Used in Salary create form.
- Used in owner salary employee filter.

Must include only seller roles:

- `PHONE_SELLER`
- `ACCESSORY_SELLER`

Do not show non-seller users.

Expected response example:

```json
{
  "success": true,
  "data": [
    {
      "id": 5,
      "username": "seller1",
      "first_name": "Ali",
      "last_name": "Valiyev",
      "role": "PHONE_SELLER",
      "branch_id": 1,
      "branch_name": "Main Branch"
    }
  ]
}
```

Flutter usage:

- Owner Salary create form uses this list.
- Owner Salary filter can use this list.
- If branch is selected, reload staff with `?branch=<branch_id>`.

---

# 3. Expense Module

## 3.1 Business Rules

Expense means a cost/expense made by sellers.

Rules:

- Expense list defaults to current month.
- Owner can view expenses for owned branches.
- Owner can filter by branch and seller.
- Owner cannot create expense.
- Owner can delete current-month expense in owned branches.
- Only sellers can create expense.
- Phone seller expense affects `PhoneCapital.current_balance`.
- Accessory seller expense affects `AccessoryCapital.current_balance`.
- Phone seller must not see accessory seller expenses.
- Accessory seller must not see phone seller expenses.
- Sellers in the same branch and same domain can see each other’s expenses.
- Sellers in different domains cannot see each other’s expenses.
- Sellers in different branches cannot see each other’s expenses.
- Expense delete is allowed only for current-month expenses.
- Past-month expense delete is blocked.
- Deleting expense rolls back capital:
  - Phone seller expense delete adds amount back to `PhoneCapital.current_balance`.
  - Accessory seller expense delete adds amount back to `AccessoryCapital.current_balance`.
- Expense must never affect another branch capital.
- Expense must never affect the wrong domain capital.

---

## 3.2 Expected API Endpoints

Use actual backend endpoints if they already exist. Expected endpoints:

```http
GET    /api/expenses/
POST   /api/expenses/
DELETE /api/expenses/<id>/
```

---

## 3.3 Expense List

Endpoint:

```http
GET /api/expenses/
```

Default:

- Returns current-month expenses.

Query params:

```text
page
q
year
month
branch      # owner only
created_by  # owner only, if backend supports it
```

Examples:

```http
GET /api/expenses/
GET /api/expenses/?year=2026&month=4
GET /api/expenses/?branch=2
GET /api/expenses/?q=transport
```

Expected response example:

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
        "name": "Transport",
        "amount": "50.00",
        "note": "Taxi",
        "branch": {
          "id": 1,
          "name": "Main Branch"
        },
        "created_by": {
          "id": 5,
          "username": "seller1"
        },
        "capital_type": "PHONE",
        "added_at": "2026-04-29T10:00:00+05:00",
        "updated_at": "2026-04-29T10:00:00+05:00"
      }
    ]
  }
}
```

Field names may differ slightly. Map safely.

---

## 3.4 Create Expense

Endpoint:

```http
POST /api/expenses/
```

Request example:

```json
{
  "name": "Transport",
  "amount": "50.00",
  "note": "Taxi"
}
```

Rules:

- Only sellers can create.
- Owner cannot create.
- Branch is resolved by backend from seller profile.
- Domain/capital type is resolved by backend from seller role.
- Flutter should not ask seller to select branch.
- Flutter should not ask seller to select domain.

Success response example:

```json
{
  "success": true,
  "data": {
    "id": 10,
    "name": "Transport",
    "amount": "50.00"
  }
}
```

After success:

- Close create sheet/dialog.
- Refresh expense list.

---

## 3.5 Delete Expense

Endpoint:

```http
DELETE /api/expenses/<id>/
```

Rules:

- Owner can delete current-month expense in owned branches.
- Seller can delete current-month expense in same branch/domain if backend allows it.
- Past-month expense delete is blocked.
- Flutter should hide delete button for past-month records when possible.
- Backend remains source of truth.

Response example:

```json
{
  "success": true,
  "data": {
    "message": "Xarajat o‘chirildi."
  }
}
```

After success:

- Refresh expense list.

---

## 3.6 Expense UI Requirements

Add page:

```text
ExpensesPage
```

Route suggestion:

```text
/expenses
```

Sidebar title:

```text
Expenses
```

Card should show:

- Expense name/title
- Amount
- Note if exists
- Branch name if available
- Created by username if available
- Added date
- Domain/capital type if useful

Actions:

- Delete button if current month and user has permission.
- No edit needed for first version.

FAB:

- Show only for sellers.
- Hide for owner.

Filters:

- Year/month
- Branch for owner
- Seller/created_by for owner if API supports
- Search if API supports

---

# 4. Salary Module

## 4.1 Business Rules

Salary means owner pays salary to sellers.

Rules:

- Only owner can create salary.
- Owner can create salary only for sellers in owned branches.
- Seller roles allowed:
  - `PHONE_SELLER`
  - `ACCESSORY_SELLER`
- Owner must not create salary for non-seller users.
- Salary create subtracts amount from selected employee branch capital:
  - Phone seller salary affects `PhoneCapital.current_balance`.
  - Accessory seller salary affects `AccessoryCapital.current_balance`.
- Owner can delete current-month salary.
- Past-month salary delete is blocked.
- Deleting salary adds amount back to correct capital.
- Sellers can only view their own salaries.
- Sellers must not see other sellers’ salaries, even in the same branch.
- Seller salary list should show current-year salaries by default.
- Owner salary list supports:
  - year filter
  - month filter
  - branch filter
  - employee/staff filter

---

## 4.2 Expected API Endpoints

Use actual backend endpoints if they already exist. Expected endpoints:

```http
GET    /api/salary/
POST   /api/salary/
DELETE /api/salary/<id>/
```

Helper APIs:

```http
GET /api/me/branches/
GET /api/me/staff/
GET /api/me/staff/?branch=<branch_id>
```

---

## 4.3 Salary List

Endpoint:

```http
GET /api/salary/
```

Default:

- Owner: current year or backend default with filters.
- Seller: current-year own salaries.

Query params:

```text
page
year
month
branch    # owner only
employee  # owner only
```

Examples:

```http
GET /api/salary/
GET /api/salary/?year=2026
GET /api/salary/?year=2026&month=4
GET /api/salary/?branch=2
GET /api/salary/?employee=5
```

Expected response example:

```json
{
  "success": true,
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 7,
        "employee": {
          "id": 5,
          "username": "seller1",
          "first_name": "Ali",
          "last_name": "Valiyev"
        },
        "branch": {
          "id": 1,
          "name": "Main Branch"
        },
        "amount": "300.00",
        "note": "April salary",
        "added_at": "2026-04-29T10:00:00+05:00",
        "updated_at": "2026-04-29T10:00:00+05:00"
      }
    ]
  }
}
```

---

## 4.4 Create Salary

Endpoint:

```http
POST /api/salary/
```

Request example:

```json
{
  "employee": 5,
  "amount": "300.00",
  "note": "April salary"
}
```

Rules:

- Only owner can create.
- Employee must be seller from owner branch.
- Backend determines correct branch/capital from employee branch role.
- Flutter must load employees from `/api/me/staff/`.
- If branch is selected, load employees from `/api/me/staff/?branch=<branch_id>`.

Response example:

```json
{
  "success": true,
  "data": {
    "id": 7,
    "amount": "300.00"
  }
}
```

After success:

- Close create sheet/dialog.
- Refresh salary list.

---

## 4.5 Delete Salary

Endpoint:

```http
DELETE /api/salary/<id>/
```

Rules:

- Owner-only.
- Only current-month salary can be deleted.
- Past-month salary delete is blocked.
- Seller cannot delete salary.

Response example:

```json
{
  "success": true,
  "data": {
    "message": "Oylik o‘chirildi."
  }
}
```

After success:

- Refresh salary list.

---

## 4.6 Salary UI Requirements

Add page:

```text
SalariesPage
```

Route suggestion:

```text
/salaries
```

Sidebar title:

```text
Salaries
```

Card should show:

- Employee full name or username
- Amount
- Branch name
- Note if exists
- Added date
- Month/year

Actions:

- Delete button only for owner and current-month record.
- Seller view is read-only.

FAB:

- Show only for owner.
- Hide for sellers.

Filters:

Owner:

- Year
- Month
- Branch
- Employee/staff

Seller:

- Year
- Month optional
- No branch filter
- No employee filter

---

# 5. Extra Profit Module

## 5.1 Business Rules

Extra Profit means additional profit added by phone sellers.

Rules:

- Extra profit list defaults to current month.
- Owner can view extra profits for owned branches.
- Owner can filter by branch.
- Owner cannot create extra profit.
- Owner can delete current-month extra profit in owned branches.
- Only `PHONE_SELLER` can create extra profit.
- `ACCESSORY_SELLER` cannot create extra profit.
- Accessory seller should not see/manage extra profit.
- Extra profit create increases `PhoneCapital.current_balance`.
- Extra profit delete subtracts amount from `PhoneCapital.current_balance`.
- Extra profit must never affect `AccessoryCapital`.
- Extra profit delete is allowed only for current-month records.
- Past-month extra profit delete is blocked.
- Phone seller can see own branch extra profits.
- Phone seller can create extra profit in own branch.
- Phone seller can delete only current-month extra profit if backend allows it.
- Backend is source of truth for final delete permission.

---

## 5.2 Expected API Endpoints

Use actual backend endpoints if they already exist. Expected endpoints:

```http
GET    /api/extra-profit/
POST   /api/extra-profit/
DELETE /api/extra-profit/<id>/
```

If backend uses another path, follow backend routes and update this document.

---

## 5.3 Extra Profit List

Endpoint:

```http
GET /api/extra-profit/
```

Default:

- Returns current-month extra profits.

Query params:

```text
page
q
year
month
branch   # owner only
```

Examples:

```http
GET /api/extra-profit/
GET /api/extra-profit/?year=2026&month=4
GET /api/extra-profit/?branch=2
```

Expected response example:

```json
{
  "success": true,
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 9,
        "amount": "40.00",
        "note": "Extra service",
        "branch": {
          "id": 1,
          "name": "Main Branch"
        },
        "created_by": {
          "id": 5,
          "username": "phone_seller"
        },
        "added_at": "2026-04-29T10:00:00+05:00",
        "updated_at": "2026-04-29T10:00:00+05:00"
      }
    ]
  }
}
```

---

## 5.4 Create Extra Profit

Endpoint:

```http
POST /api/extra-profit/
```

Request example:

```json
{
  "amount": "40.00",
  "note": "Extra service"
}
```

Rules:

- Only phone seller can create.
- Owner cannot create.
- Accessory seller cannot create.
- Branch is resolved by backend from phone seller profile.
- On success, `PhoneCapital.current_balance` increases.

Response example:

```json
{
  "success": true,
  "data": {
    "id": 9,
    "amount": "40.00"
  }
}
```

After success:

- Close create sheet/dialog.
- Refresh extra profit list.

---

## 5.5 Delete Extra Profit

Endpoint:

```http
DELETE /api/extra-profit/<id>/
```

Rules:

- Owner can delete current-month extra profit in owned branches.
- Phone seller can delete current-month extra profit if backend allows.
- Accessory seller is blocked.
- Past-month delete is blocked.
- On delete, `PhoneCapital.current_balance` decreases.

Response example:

```json
{
  "success": true,
  "data": {
    "message": "Qo‘shimcha foyda o‘chirildi."
  }
}
```

After success:

- Refresh extra profit list.

---

## 5.6 Extra Profit UI Requirements

Add page:

```text
ExtraProfitPage
```

Route suggestion:

```text
/extra-profits
```

Sidebar title:

```text
Extra Profit
```

Card should show:

- Amount
- Note if exists
- Branch name if available
- Created by username if available
- Added date

Actions:

- Delete button if current-month and backend permission allows.
- No edit needed for first version.

FAB:

- Show only for phone sellers.
- Hide for owner.
- Hide for accessory sellers.

Filters:

- Year/month
- Branch for owner
- Search if backend supports

---

# 6. Shared UI Components

Try to reuse components across modules.

Suggested shared widgets:

```text
shared/widgets/app_floating_add_button.dart
shared/widgets/filter_section.dart
shared/widgets/empty_state.dart
shared/widgets/error_state.dart
shared/widgets/loading_state.dart
shared/widgets/confirm_delete_dialog.dart
```

If existing shared widgets already exist, reuse them instead of creating duplicates.

---

# 7. Refresh Rules

After any successful mutation:

## Expense

- Create expense -> refresh expense list.
- Delete expense -> refresh expense list.

## Salary

- Create salary -> refresh salary list.
- Delete salary -> refresh salary list.

## Extra Profit

- Create extra profit -> refresh extra profit list.
- Delete extra profit -> refresh extra profit list.

Also keep pull-to-refresh on every list page.

---

# 8. Error Handling

Show backend errors clearly.

Examples:

- “Sizga bu amalni bajarish mumkin emas.”
- “Faqat joriy oy yozuvini o‘chirish mumkin.”
- “Summa noldan katta bo‘lishi kerak.”
- “Owner cannot create expense.”
- “Accessory seller cannot create extra profit.”

Do not show stack traces.

Use SnackBar or clean inline error UI.

---

# 9. Code Organization

Use existing feature-based structure.

Add these feature folders if missing:

```text
lib/features/expenses/
  data/
    models/
    repositories/
  presentation/
    providers/
    pages/
    widgets/

lib/features/salaries/
  data/
    models/
    repositories/
  presentation/
    providers/
    pages/
    widgets/

lib/features/extra_profit/
  data/
    models/
    repositories/
  presentation/
    providers/
    pages/
    widgets/
```

Use existing project patterns from:

- phones
- accessories
- debts

Do not introduce a completely different architecture.

---

# 10. Routes

Add routes inside existing shell/app layout:

```text
/expenses
/salaries
/extra-profits
```

Make sure:

- Drawer closes after navigation.
- Routes are protected by auth.
- PIN/auth flow is not broken.

---

# 11. Implementation Checklist

## Expense

- [ ] Expense model
- [ ] Expense repository
- [ ] Expense provider
- [ ] Expense list page
- [ ] Expense create sheet
- [ ] Expense delete action
- [ ] Expense filters
- [ ] Sidebar item
- [ ] Refresh after create/delete

## Salary

- [ ] Salary model
- [ ] Salary repository
- [ ] Owner staff model
- [ ] Owner branches model if not existing
- [ ] Salary provider
- [ ] Salary list page
- [ ] Salary create sheet
- [ ] Salary delete action
- [ ] Salary filters
- [ ] Sidebar item
- [ ] Refresh after create/delete

## Extra Profit

- [ ] Extra profit model
- [ ] Extra profit repository
- [ ] Extra profit provider
- [ ] Extra profit list page
- [ ] Extra profit create sheet
- [ ] Extra profit delete action
- [ ] Extra profit filters
- [ ] Sidebar item
- [ ] Refresh after create/delete

---

# 12. Validation Before Finish

Run:

```bash
dart format lib/
flutter analyze
```

If tests exist:

```bash
flutter test
```

Final report must include:

- changed files
- routes added
- pages added
- providers added
- repositories added
- API endpoints used
- commands run
- remaining issues
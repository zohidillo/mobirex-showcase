<!-- markdownlint-disable -->
# Mobirex

CRM/ERP for phone and accessory retail shops in Uzbekistan.

![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-API-red)
![Flutter](https://img.shields.io/badge/Flutter-mobile-02569B?logo=flutter&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-database-336791?logo=postgresql&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0)

## What this repository is

The working codebase of Mobirex, running in production for phone and accessory
retail shops in Uzbekistan: a Django/DRF backend, a Flutter mobile app, a
Telegram support bot, and a static landing site. Secrets are removed;
`.env.example` files show how each component is configured.

## The problem

Phone shops in Uzbekistan track sales, stock, and customer debt in paper
notebooks, Excel, or Telegram messages. At month end the cash does not add
up and nobody can say where it went. The owner cannot answer who sold what,
how much cash is in which branch, or who owes money.

## The solution

Mobirex gives each shop a branch-scoped CRM: phone and accessory inventory
with separate capital pools, sales and debt tracking, role-based staff
accounts, a monthly close that snapshots and locks a branch's financials,
and a mobile app for sellers to work from the shop floor.

## Screenshots

| Login | Menu | Staff | Phones |
|---|---|---|---|
| ![](screenshots/01-login.png) | ![](screenshots/02-menu.png) | ![](screenshots/03-staff.png) | ![](screenshots/04-phones.png) |

## Repository structure

```
mobirex-showcase/
├── backend/    Django 5.2 + DRF API, PostgreSQL, Celery, Redis
├── mobile/     Flutter app (Riverpod, GoRouter, Dio)
├── bot/        aiogram 3.x Telegram support bot
└── landing/    Static landing site (UZ/RU/EN)
```

## Architecture

- **Service layer** — `backend/src/services/` holds all business logic
  (`create.py`, `sell.py`, `payment.py` per domain); views stay thin and
  call services, never touch models directly for writes.
- **Multi-tenancy** — isolation is branch → role → domain. A user belongs to
  a branch and a role (owner, phone seller, accessory seller); each role
  only sees its own domain's data within its branch.
- **Month close** — `backend/src/services/month_closing/service.py` closes a
  branch's month: snapshots totals, freezes the period, and must be
  idempotent — running it twice must not double-charge capital or double-
  count a snapshot. Backed by `transaction.atomic` + `select_for_update`.

## Technical highlights

- **Idempotent month close** — [`backend/src/services/month_closing/service.py`](backend/src/services/month_closing/service.py).
  Closing the same month twice (retry, double-click, concurrent request)
  must produce the same result, not a duplicated snapshot or a second
  capital deduction. Guarded with row locking and covered by
  [`backend/tests/test_month_closing_race.py`](backend/tests/test_month_closing_race.py).
- **Separate capital pools** — [`backend/src/services/capital/capital_service.py`](backend/src/services/capital/capital_service.py).
  Phone capital and accessory capital are tracked and reported independently
  per branch, even though both feed the same owner. See
  [`backend/tests/test_capital_isolation.py`](backend/tests/test_capital_isolation.py).
- **Role and domain isolation** — [`backend/src/shared/permissions.py`](backend/src/shared/permissions.py).
  A phone seller cannot see accessory data in the same branch, and vice
  versa, enforced at the permission layer, not just the UI.
- **Subscription billing** — [`backend/src/services/billing/daily_charge.py`](backend/src/services/billing/daily_charge.py),
  [`grace_status.py`](backend/src/services/billing/grace_status.py). Daily charge
  against a branch's balance, a grace period on non-payment, then automatic
  access blocking.
- **Centralized error reporting** — [`backend/src/services/error_reporting/`](backend/src/services/error_reporting/).
  Backend and mobile errors are deduplicated by fingerprint, rate-limited,
  and forwarded to Telegram so the team hears about production issues in
  real time without spamming a channel on every occurrence.
- **Offline-tolerant mobile client** — [`mobile/lib/core/network/dio_client.dart`](mobile/lib/core/network/dio_client.dart),
  [`interceptors/auth_interceptor.dart`](mobile/lib/core/network/interceptors/auth_interceptor.dart).
  Token refresh is queued so concurrent requests don't each trigger their
  own refresh, and network/API errors are normalized before reaching the UI.

## Running locally

```bash
cp backend/.env.example backend/.env
cp bot/.env.example bot/.env
# fill in the values, then:
cd backend && docker compose up
```

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2, Django REST Framework, PostgreSQL, Celery, Redis |
| Mobile | Flutter, Riverpod, GoRouter, Dio |
| Bot | Python, aiogram 3.x |
| Landing | Static HTML/CSS/JS (UZ/RU/EN) |
| Infra | Docker, nginx, Let's Encrypt |

## Status

- Landing site live at `mobirex.uz`
- Backend API live at `api.mobirex.uz`
- Android: internal testing track on Google Play, not publicly listed
- iOS: submitted to the App Store, under review, not yet approved
- No paying customers yet

## Author

Built solo by Zohidillo Turgunov.

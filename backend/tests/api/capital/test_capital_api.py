"""Capital API tests covering all business rules."""

from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from src.core import models


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _capital(model_name, branch, **kwargs):
    defaults = {
        "month": timezone.localdate().replace(day=1),
        "invested_amount": Decimal("100.00"),
        "current_balance": Decimal("60.00"),
    }
    defaults.update(kwargs)
    model = getattr(models, model_name)
    return model.objects.create(branch=branch, **defaults)


def _past_month():
    today = timezone.localdate()
    if today.month == 1:
        return date(today.year - 1, 12, 1)
    return date(today.year, today.month - 1, 1)


# ===========================================================================
# ACCESSORY CAPITAL — view-only, owner only
# ===========================================================================

class TestAccessoryCapitalList:
    """Tests #1–#7: accessory capital list rules."""

    # 1. Owner can list accessory capital for owned branches
    def test_owner_sees_only_owned_accessory_capital(self, api_client, users, branches):
        own = _capital("AccessoryCapital", branches["main"])
        other = _capital("AccessoryCapital", branches["other"], current_balance=Decimal("44.00"))

        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_accessory_capital_list"))

        assert res.status_code == 200
        ids = {row["id"] for row in res.json()["data"]["results"]}
        assert own.id in ids
        assert other.id not in ids  # other_branch not linked to owner via BranchUser

    # 2. Owner branch filter works
    def test_owner_accessory_capital_branch_filter(self, api_client, users, branches):
        capital_factory_fn = lambda: _capital("AccessoryCapital", branches["main"])
        cap = capital_factory_fn()

        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(
            reverse("api_accessory_capital_list"),
            {"branch": branches["main"].id},
        )

        assert res.status_code == 200
        ids = {row["id"] for row in res.json()["data"]["results"]}
        assert cap.id in ids

    # 3. Owner cannot view non-owned branch capital (covered by test 1: other_branch excluded)

    # 4. Phone seller blocked from accessory capital
    def test_phone_seller_blocked_from_accessory_capital(self, api_client, users):
        api_client.force_authenticate(user=users["phone_seller"])
        res = api_client.get(reverse("api_accessory_capital_list"))
        assert res.status_code == 403

    # 5. Accessory seller blocked from accessory capital
    def test_accessory_seller_blocked_from_accessory_capital(self, api_client, users):
        api_client.force_authenticate(user=users["accessory_seller"])
        res = api_client.get(reverse("api_accessory_capital_list"))
        assert res.status_code == 403

    # 6. POST accessory capital not allowed (405 Method Not Allowed)
    def test_post_accessory_capital_not_allowed(self, api_client, users):
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(reverse("api_accessory_capital_list"), {"branch": 1, "amount": "1000"})
        assert res.status_code == 405

    # 7. List defaults to current year, max 12 monthly rows per branch/year
    def test_accessory_capital_year_filter_and_max_12_months(self, api_client, users, branches):
        today = timezone.localdate()
        current_year = today.year
        for m in range(1, 13):
            models.AccessoryCapital.objects.get_or_create(
                branch=branches["main"],
                month=date(current_year, m, 1),
                defaults={"invested_amount": Decimal("10.00"), "current_balance": Decimal("5.00")},
            )

        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_accessory_capital_list"), {"year": current_year})

        assert res.status_code == 200
        results = res.json()["data"]["results"]
        assert len(results) <= 12

    def test_accessory_capital_current_month_first(self, api_client, users, branches):
        today = timezone.localdate()
        current_month = today.replace(day=1)
        past_month = _past_month()

        _capital("AccessoryCapital", branches["main"], month=past_month)
        cap_current = _capital("AccessoryCapital", branches["main"], month=current_month)

        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_accessory_capital_list"))

        assert res.status_code == 200
        results = res.json()["data"]["results"]
        assert results[0]["id"] == cap_current.id

    def test_owner_accessory_capital_has_inventory_value(
        self, api_client, users, branches, accessory_factory
    ):
        """Accessory capital serializer includes inventory_value calculated from stock."""
        capital = _capital(
            "AccessoryCapital", branches["main"],
            invested_amount=Decimal("80.00"),
            current_balance=Decimal("35.00"),
        )
        accessory_factory(branch=branches["main"], stock=3, unit_cost=Decimal("10.00"))
        accessory_factory(branch=branches["main"], stock=2, unit_cost=Decimal("7.50"))

        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_accessory_capital_list"))

        assert res.status_code == 200
        results = res.json()["data"]["results"]
        row = next(r for r in results if r["id"] == capital.id)
        assert row["invested_amount"] == "80.00"
        assert row["current_balance"] == "35.00"
        assert row["inventory_value"] == "45.00"

    def test_accessory_capital_response_has_timestamps(self, api_client, users, branches):
        _capital("AccessoryCapital", branches["main"])
        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_accessory_capital_list"))
        assert res.status_code == 200
        row = res.json()["data"]["results"][0]
        assert "added_at" in row
        assert "updated_at" in row


# ===========================================================================
# PHONE CAPITAL — list
# ===========================================================================

class TestPhoneCapitalList:
    """Tests #8–#12: phone capital list rules."""

    # 8. Owner can list phone capital for owned branches
    def test_owner_sees_only_owned_phone_capital(self, api_client, users, branches):
        main_cap = _capital("PhoneCapital", branches["main"], invested_amount=Decimal("150.00"))
        other_cap = _capital("PhoneCapital", branches["other"], invested_amount=Decimal("200.00"))

        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_phone_capital_list"))

        assert res.status_code == 200
        ids = {row["id"] for row in res.json()["data"]["results"] if row["id"] is not None}
        assert main_cap.id in ids
        assert other_cap.id not in ids

    # 9. Owner branch filter works
    def test_owner_phone_capital_branch_filter(self, api_client, users, branches):
        cap = _capital("PhoneCapital", branches["main"])
        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(
            reverse("api_phone_capital_list"), {"branch": branches["main"].id}
        )
        assert res.status_code == 200
        ids = {row["id"] for row in res.json()["data"]["results"] if row["id"] is not None}
        assert cap.id in ids

    def test_owner_branch_filter_rejects_non_owned_branch(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(
            reverse("api_phone_capital_list"), {"branch": branches["other"].id}
        )
        assert res.status_code == 403

    # 11. Phone seller blocked from phone capital
    def test_phone_seller_blocked_from_phone_capital(self, api_client, users):
        api_client.force_authenticate(user=users["phone_seller"])
        res = api_client.get(reverse("api_phone_capital_list"))
        assert res.status_code == 403

    def test_accessory_seller_blocked_from_phone_capital(self, api_client, users):
        api_client.force_authenticate(user=users["accessory_seller"])
        res = api_client.get(reverse("api_phone_capital_list"))
        assert res.status_code == 403

    # 12. List defaults to current year, current month first, max 12 rows per branch/year
    def test_phone_capital_year_filter_and_max_12_months(self, api_client, users, branches):
        today = timezone.localdate()
        current_year = today.year
        for m in range(1, 13):
            models.PhoneCapital.objects.get_or_create(
                branch=branches["main"],
                month=date(current_year, m, 1),
                defaults={"invested_amount": Decimal("10.00"), "current_balance": Decimal("5.00")},
            )

        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_phone_capital_list"), {"year": current_year})

        assert res.status_code == 200
        results = res.json()["data"]["results"]
        assert len(results) <= 12

    def test_phone_capital_current_month_first(self, api_client, users, branches):
        today = timezone.localdate()
        current_month = today.replace(day=1)
        past_month = _past_month()

        _capital("PhoneCapital", branches["main"], month=past_month)
        cap_current = _capital("PhoneCapital", branches["main"], month=current_month)

        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_phone_capital_list"))

        assert res.status_code == 200
        results = res.json()["data"]["results"]
        assert results[0]["id"] == cap_current.id

    def test_phone_capital_placeholder_for_missing_current_month(self, api_client, users, branches):
        """Owner sees a placeholder row (id=null) when no current-month capital exists."""
        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_phone_capital_list"))
        assert res.status_code == 200
        results = res.json()["data"]["results"]
        placeholders = [r for r in results if r["id"] is None]
        assert len(placeholders) >= 1

    def test_phone_capital_response_has_timestamps(self, api_client, users, branches):
        _capital("PhoneCapital", branches["main"])
        api_client.force_authenticate(user=users["owner"])
        res = api_client.get(reverse("api_phone_capital_list"))
        assert res.status_code == 200
        real_rows = [r for r in res.json()["data"]["results"] if r["id"] is not None]
        if real_rows:
            assert "added_at" in real_rows[0]
            assert "updated_at" in real_rows[0]


# ===========================================================================
# PHONE CAPITAL — add investment
# ===========================================================================

class TestPhoneCapitalAdd:
    """Tests #13–#20: phone capital investment add rules."""

    # 13 + 14. Owner can add investment; creates row when missing
    def test_owner_add_investment_creates_row(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        assert not models.PhoneCapital.objects.filter(
            branch=branches["main"], month=timezone.localdate().replace(day=1)
        ).exists()

        res = api_client.post(
            reverse("api_phone_capital_list"),
            {"branch": branches["main"].id, "amount": "10000.00"},
        )
        assert res.status_code == 201
        data = res.json()["data"]
        assert Decimal(data["invested_amount"]) == Decimal("10000.00")
        assert Decimal(data["current_balance"]) == Decimal("10000.00")

        capital = models.PhoneCapital.objects.get(
            branch=branches["main"], month=timezone.localdate().replace(day=1)
        )
        assert capital.invested_amount == Decimal("10000.00")

    # 15 + 16. Second add in same month accumulates invested_amount and current_balance
    def test_owner_add_investment_accumulates(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        url = reverse("api_phone_capital_list")

        api_client.post(url, {"branch": branches["main"].id, "amount": "10000.00"})
        api_client.post(url, {"branch": branches["main"].id, "amount": "5000.00"})

        capital = models.PhoneCapital.objects.get(
            branch=branches["main"], month=timezone.localdate().replace(day=1)
        )
        assert capital.invested_amount == Decimal("15000.00")
        assert capital.current_balance == Decimal("15000.00")

    # 17. Client cannot send month or year
    def test_add_investment_rejects_month_field(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(
            reverse("api_phone_capital_list"),
            {"branch": branches["main"].id, "amount": "1000.00", "month": "2025-01-01"},
        )
        assert res.status_code == 400

    def test_add_investment_rejects_year_field(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(
            reverse("api_phone_capital_list"),
            {"branch": branches["main"].id, "amount": "1000.00", "year": "2025"},
        )
        assert res.status_code == 400

    # 18. Owner cannot add to non-owned branch
    def test_owner_cannot_add_to_non_owned_branch(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(
            reverse("api_phone_capital_list"),
            {"branch": branches["other"].id, "amount": "1000.00"},
        )
        assert res.status_code in (400, 403)

    # 19. Sellers cannot add phone capital
    def test_phone_seller_cannot_add_investment(self, api_client, users, branches):
        api_client.force_authenticate(user=users["phone_seller"])
        res = api_client.post(
            reverse("api_phone_capital_list"),
            {"branch": branches["main"].id, "amount": "1000.00"},
        )
        assert res.status_code == 403

    def test_accessory_seller_cannot_add_investment(self, api_client, users, branches):
        api_client.force_authenticate(user=users["accessory_seller"])
        res = api_client.post(
            reverse("api_phone_capital_list"),
            {"branch": branches["main"].id, "amount": "1000.00"},
        )
        assert res.status_code == 403

    # 20. Amount must be positive
    def test_add_investment_amount_must_be_positive(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        for bad_amount in ["0", "-100", "0.00", "-0.01"]:
            res = api_client.post(
                reverse("api_phone_capital_list"),
                {"branch": branches["main"].id, "amount": bad_amount},
            )
            assert res.status_code == 400, f"Expected 400 for amount={bad_amount}"

    def test_add_investment_missing_branch_returns_400(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(reverse("api_phone_capital_list"), {"amount": "1000.00"})
        assert res.status_code == 400

    def test_add_investment_uses_current_month(self, api_client, users, branches):
        """Verify the created row has month=first day of current month."""
        api_client.force_authenticate(user=users["owner"])
        api_client.post(
            reverse("api_phone_capital_list"),
            {"branch": branches["main"].id, "amount": "500.00"},
        )
        capital = models.PhoneCapital.objects.get(
            branch=branches["main"], month=timezone.localdate().replace(day=1)
        )
        assert capital.month == timezone.localdate().replace(day=1)


# ===========================================================================
# PHONE CAPITAL — reset
# ===========================================================================

class TestPhoneCapitalReset:
    """Tests #21–#27: phone capital reset rules."""

    # 21–23. Owner can reset: invested_amount=0, balance -= old invested
    def test_owner_reset_current_month(self, api_client, users, branches):
        capital = _capital(
            "PhoneCapital", branches["main"],
            invested_amount=Decimal("15000.00"),
            current_balance=Decimal("12000.00"),
        )
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(
            reverse("api_phone_capital_reset"), {"branch": branches["main"].id}
        )

        assert res.status_code == 200
        capital.refresh_from_db()
        assert capital.invested_amount == Decimal("0.00")
        assert capital.current_balance == Decimal("-3000.00")

    def test_reset_invested_becomes_zero(self, api_client, users, branches):
        _capital(
            "PhoneCapital", branches["main"],
            invested_amount=Decimal("5000.00"),
            current_balance=Decimal("4000.00"),
        )
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(
            reverse("api_phone_capital_reset"), {"branch": branches["main"].id}
        )
        assert res.status_code == 200
        assert Decimal(res.json()["data"]["invested_amount"]) == Decimal("0.00")

    def test_reset_balance_subtracts_old_invested(self, api_client, users, branches):
        _capital(
            "PhoneCapital", branches["main"],
            invested_amount=Decimal("8000.00"),
            current_balance=Decimal("6000.00"),
        )
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(
            reverse("api_phone_capital_reset"), {"branch": branches["main"].id}
        )
        assert res.status_code == 200
        assert Decimal(res.json()["data"]["current_balance"]) == Decimal("-2000.00")

    # 24. Reset does not touch product records
    def test_reset_does_not_touch_phone_records(self, api_client, users, branches, phone_factory):
        _capital("PhoneCapital", branches["main"], invested_amount=Decimal("5000.00"))
        phone = phone_factory(branch=branches["main"])

        api_client.force_authenticate(user=users["owner"])
        api_client.post(reverse("api_phone_capital_reset"), {"branch": branches["main"].id})

        phone.refresh_from_db()
        assert not phone.is_deleted

    # 25. Owner cannot reset non-owned branch
    def test_owner_cannot_reset_non_owned_branch(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(
            reverse("api_phone_capital_reset"), {"branch": branches["other"].id}
        )
        assert res.status_code in (400, 403)

    # 26. Sellers cannot reset
    def test_phone_seller_cannot_reset(self, api_client, users, branches):
        api_client.force_authenticate(user=users["phone_seller"])
        res = api_client.post(
            reverse("api_phone_capital_reset"), {"branch": branches["main"].id}
        )
        assert res.status_code == 403

    def test_accessory_seller_cannot_reset(self, api_client, users, branches):
        api_client.force_authenticate(user=users["accessory_seller"])
        res = api_client.post(
            reverse("api_phone_capital_reset"), {"branch": branches["main"].id}
        )
        assert res.status_code == 403

    # 27. Past-month reset not possible (no current-month capital → error)
    def test_reset_returns_error_when_no_current_month_capital(
        self, api_client, users, branches
    ):
        """If no current-month row exists for the branch, reset returns 400."""
        _capital("PhoneCapital", branches["main"], month=_past_month())
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(
            reverse("api_phone_capital_reset"), {"branch": branches["main"].id}
        )
        assert res.status_code == 400

    def test_reset_missing_branch_returns_400(self, api_client, users, branches):
        api_client.force_authenticate(user=users["owner"])
        res = api_client.post(reverse("api_phone_capital_reset"), {})
        assert res.status_code == 400


# ===========================================================================
# Unauthenticated access
# ===========================================================================

class TestCapitalUnauthorized:
    def test_unauthenticated_blocked_from_phone_capital(self, api_client):
        res = api_client.get(reverse("api_phone_capital_list"))
        assert res.status_code in (401, 403)

    def test_unauthenticated_blocked_from_accessory_capital(self, api_client):
        res = api_client.get(reverse("api_accessory_capital_list"))
        assert res.status_code in (401, 403)

    def test_outsider_blocked_from_phone_capital(self, api_client, users):
        api_client.force_authenticate(user=users["outsider"])
        assert api_client.get(reverse("api_phone_capital_list")).status_code == 403

    def test_outsider_blocked_from_accessory_capital(self, api_client, users):
        api_client.force_authenticate(user=users["outsider"])
        assert api_client.get(reverse("api_accessory_capital_list")).status_code == 403

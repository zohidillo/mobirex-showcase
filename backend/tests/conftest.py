from datetime import datetime
from decimal import Decimal

import pytest
from django.utils import timezone


@pytest.fixture
def api_client():
    """Return a DRF API client."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def users(db):
    """Create reusable API test users."""
    from src.core import models

    return {
        "admin": models.User.objects.create_superuser(username="admin_api", password="pass123"),
        "owner": models.User.objects.create_user(username="owner_api", password="pass123"),
        "phone_seller": models.User.objects.create_user(
            username="phone_seller_api",
            password="pass123",
        ),
        "accessory_seller": models.User.objects.create_user(
            username="accessory_seller_api",
            password="pass123",
        ),
        "cashier": models.User.objects.create_user(
            username="cashier_api",
            password="pass123",
            is_cashier=True,
        ),
        "outsider": models.User.objects.create_user(username="outsider_api", password="pass123"),
    }


@pytest.fixture
def branches(db, users):
    """Create reusable API test branches."""
    from src.core import models

    main_branch = models.Branch.objects.create(name="Main Branch", owner=users["owner"])
    other_branch = models.Branch.objects.create(name="Other Branch", owner=users["owner"])

    models.BranchUser.objects.create(
        user=users["owner"],
        branch=main_branch,
        role=models.BranchUser.ROLE_OWNER,
    )
    models.BranchUser.objects.create(
        user=users["phone_seller"],
        branch=main_branch,
        role=models.BranchUser.ROLE_PHONE_SELLER,
    )
    models.BranchUser.objects.create(
        user=users["accessory_seller"],
        branch=main_branch,
        role=models.BranchUser.ROLE_ACCESSORY_SELLER,
    )

    return {
        "main": main_branch,
        "other": other_branch,
    }


@pytest.fixture
def categories(db):
    """Create reusable API test categories."""
    from src.core import models

    return {
        "phone": models.PhoneCategory.objects.create(name="Smartphones"),
        "accessory": models.AccessoryCategory.objects.create(name="Cases"),
    }


@pytest.fixture
def set_model_datetime():
    """Allow tests to override auto-managed timestamps."""

    def _set(instance, **values):
        instance.__class__.all_objects.filter(pk=instance.pk).update(**values)
        instance.refresh_from_db()
        return instance

    return _set


@pytest.fixture
def time_points():
    """Provide current and previous month timestamps."""
    today = timezone.localdate()
    current = timezone.make_aware(datetime(today.year, today.month, 20, 10, 0, 0))

    if today.month == 1:
        previous_year = today.year - 1
        previous_month = 12
    else:
        previous_year = today.year
        previous_month = today.month - 1

    previous = timezone.make_aware(datetime(previous_year, previous_month, 15, 10, 0, 0))
    return {
        "current": current,
        "previous": previous,
    }


@pytest.fixture
def phone_factory(db, branches, categories, users):
    """Create phones for API tests."""
    from src.core import models

    def _create(**overrides):
        defaults = {
            "name": "Phone Model",
            "category": categories["phone"],
            "branch": branches["main"],
            "imei": f"IMEI-{models.Phone.all_objects.count() + 1:06d}",
            "storage": "128",
            "color": "Black",
            "from_by": "Supplier",
            "cost_price": Decimal("500.00"),
            "added_by": users["owner"],
        }
        defaults.update(overrides)
        return models.Phone.objects.create(**defaults)

    return _create


@pytest.fixture
def accessory_factory(db, branches, categories, users):
    """Create accessories for API tests."""
    from src.core import models

    def _create(**overrides):
        defaults = {
            "name": f"Accessory {models.Accessory.all_objects.count() + 1}",
            "category": categories["accessory"],
            "branch": branches["main"],
            "unit_cost": Decimal("10.00"),
            "stock": 5,
            "added_by": users["owner"],
            "is_active": True,
        }
        defaults.update(overrides)
        return models.Accessory.objects.create(**defaults)

    return _create


@pytest.fixture
def debt_factory(db, branches, users):
    """Create debts for API tests."""
    from src.core import models

    def _create(**overrides):
        defaults = {
            "branch": branches["main"],
            "created_by": users["phone_seller"],
            "f_name": f"Debt {models.Debt.all_objects.count() + 1}",
            "amount": Decimal("100.00"),
            "remaining_amount": Decimal("100.00"),
            "direction": "WE_GAVE",
            "note": "API debt",
        }
        defaults.update(overrides)
        return models.Debt.objects.create(**defaults)

    return _create


@pytest.fixture
def expense_factory(db, branches, users):
    """Create expenses for API tests."""
    from src.core import models

    def _create(**overrides):
        defaults = {
            "branch": branches["main"],
            "created_by": users["phone_seller"],
            "type": "SHOP_EXPENSE",
            "amount": Decimal("10.00"),
            "note": "API expense",
        }
        defaults.update(overrides)
        return models.Expense.objects.create(**defaults)

    return _create


@pytest.fixture
def salary_factory(db, branches, users):
    """Create salaries for API tests."""
    from src.core import models

    def _create(**overrides):
        defaults = {
            "branch": branches["main"],
            "employee": users["phone_seller"],
            "created_by": users["owner"],
            "amount": Decimal("50.00"),
            "note": "API salary",
        }
        defaults.update(overrides)
        return models.Salary.objects.create(**defaults)

    return _create


@pytest.fixture
def extra_profit_factory(db, branches, users):
    """Create extra profit rows for API tests."""
    from src.core import models

    def _create(**overrides):
        defaults = {
            "branch": branches["main"],
            "created_by": users["owner"],
            "amount": Decimal("20.00"),
            "note": "API extra profit",
        }
        defaults.update(overrides)
        return models.ExtraProfit.objects.create(**defaults)

    return _create


@pytest.fixture
def capital_factory(db, branches):
    """Create capital rows for API tests."""
    from src.core import models

    def _create(model_name, **overrides):
        model = getattr(models, model_name)
        defaults = {
            "branch": branches["main"],
            "month": timezone.localdate().replace(day=1),
            "invested_amount": Decimal("100.00"),
            "current_balance": Decimal("60.00"),
        }
        defaults.update(overrides)
        return model.objects.create(**defaults)

    return _create


@pytest.fixture
def journal_factory(db, branches, users):
    """Create journal rows for API tests."""
    from src.core import models

    def _create(**overrides):
        defaults = {
            "branch": branches["main"],
            "user": users["phone_seller"],
            "action": "CREATE",
            "model_name": "phone",
            "object_id": models.Journal.objects.count() + 1,
            "object_repr": "Journal object",
            "old_data": None,
            "new_data": {"amount": "10.00", "name": "Journal object"},
        }
        defaults.update(overrides)
        return models.Journal.objects.create(**defaults)

    return _create


@pytest.fixture
def payment_factory(db, users):
    """Create billing payments for API tests."""
    from src.core import models

    def _create(**overrides):
        defaults = {
            "user": users["phone_seller"],
            "amount": Decimal("100.00"),
            "payment_type": "cash",
            "added_by": users["cashier"],
        }
        defaults.update(overrides)
        return models.Payment.objects.create(**defaults)

    return _create


@pytest.fixture
def transaction_log_factory(db, users):
    """Create transaction logs for API tests."""
    from src.core import models

    def _create(**overrides):
        defaults = {
            "user": users["phone_seller"],
            "type": "payment",
            "amount": Decimal("50.00"),
            "balance_before": Decimal("10.00"),
            "balance_after": Decimal("60.00"),
        }
        defaults.update(overrides)
        return models.TransactionLog.objects.create(**defaults)

    return _create

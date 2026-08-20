import json
from datetime import datetime
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.test import force_authenticate

from src.api.base import BaseAPIView
from src.api.responses import error_response, success_response
from src.core import models
from src.shared.filters import get_filtered_queryset
from src.shared.paginations import StandardPagination
from src.shared.permissions import (
    can_access_branch,
    is_accessory_seller,
    is_owner,
    is_phone_seller,
)
from src.shared.validators import (
    check_stock_available,
    validate_branch_access,
    validate_debt_payment,
    validate_positive_amount,
)


class SampleAPIView(BaseAPIView):
    """Provide a simple success response for tests."""

    def get(self, request, *args, **kwargs):
        """Return a basic success payload."""
        return self.success({"message": "ok"})


class BrokenAPIView(BaseAPIView):
    """Raise a validation error for tests."""

    def get(self, request, *args, **kwargs):
        """Raise a validation error."""
        raise ValidationError("bad input")


class APIInfrastructureTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.owner = models.User.objects.create_user(username="owner_api", password="pass123")
        self.phone_seller = models.User.objects.create_user(
            username="phone_seller_api",
            password="pass123",
        )
        self.accessory_seller = models.User.objects.create_user(
            username="accessory_seller_api",
            password="pass123",
        )
        self.employee = models.User.objects.create_user(username="employee_api", password="pass123")
        self.other_user = models.User.objects.create_user(username="other_api", password="pass123")

        self.branch = models.Branch.objects.create(name="API Branch", owner=self.owner)
        models.BranchUser.objects.create(
            user=self.owner,
            branch=self.branch,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=self.phone_seller,
            branch=self.branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        models.BranchUser.objects.create(
            user=self.accessory_seller,
            branch=self.branch,
            role=models.BranchUser.ROLE_ACCESSORY_SELLER,
        )

        self.accessory_category = models.AccessoryCategory.objects.create(name="API Cases")
        self.accessory = models.Accessory.objects.create(
            name="API Case",
            category=self.accessory_category,
            branch=self.branch,
            unit_cost=Decimal("10.00"),
            stock=5,
            added_by=self.owner,
        )
        self.debt = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.phone_seller,
            f_name="API Debt",
            amount=Decimal("120.00"),
            remaining_amount=Decimal("120.00"),
            direction="WE_GAVE",
        )

    def _set_added_at(self, instance, value):
        instance.__class__.all_objects.filter(pk=instance.pk).update(
            added_at=value,
            updated_at=value,
        )
        instance.refresh_from_db()

    def _decode(self, response):
        return json.loads(response.content.decode("utf-8"))

    def test_validation_helpers_work(self):
        self.assertEqual(validate_positive_amount("12.50"), Decimal("12.50"))
        self.assertEqual(check_stock_available(self.accessory, 3), Decimal("3"))
        self.assertEqual(validate_debt_payment(self.debt, "40"), Decimal("40"))
        self.assertEqual(validate_branch_access(self.owner, self.branch), self.branch)

        self.assertTrue(is_owner(self.owner))
        self.assertTrue(is_phone_seller(self.phone_seller))
        self.assertTrue(is_accessory_seller(self.accessory_seller))
        self.assertTrue(can_access_branch(self.owner, self.branch))

        with self.assertRaises(ValidationError):
            validate_positive_amount("0")
        with self.assertRaises(ValidationError):
            check_stock_available(self.accessory, 99)
        with self.assertRaises(ValidationError):
            validate_debt_payment(self.debt, 999)
        with self.assertRaises(PermissionDenied):
            validate_branch_access(self.other_user, self.branch)

    def test_date_filtering_has_no_default_month_restriction(self):
        current_payment = models.Payment.objects.create(
            user=self.owner,
            amount=Decimal("100.00"),
            payment_type="cash",
            added_by=self.owner,
        )
        previous_payment = models.Payment.objects.create(
            user=self.owner,
            amount=Decimal("80.00"),
            payment_type="cash",
            added_by=self.owner,
        )
        previous_month = timezone.make_aware(datetime(2026, 2, 15, 10, 0, 0))
        self._set_added_at(previous_payment, previous_month)

        request = self.factory.get("/api/")
        filtered = get_filtered_queryset(
            models.Payment.objects.filter(pk__in=[current_payment.pk, previous_payment.pk]),
            request,
        )

        filtered_ids = set(filtered.values_list("id", flat=True))
        self.assertIn(current_payment.id, filtered_ids)
        self.assertIn(previous_payment.id, filtered_ids)

    def test_date_filtering_honors_explicit_year_month_and_keeps_default_unfiltered(self):
        current_payment = models.Payment.objects.create(
            user=self.owner,
            amount=Decimal("100.00"),
            payment_type="cash",
            added_by=self.owner,
        )
        previous_payment = models.Payment.objects.create(
            user=self.owner,
            amount=Decimal("80.00"),
            payment_type="cash",
            added_by=self.owner,
        )
        previous_month = timezone.make_aware(datetime(2026, 2, 15, 10, 0, 0))
        self._set_added_at(previous_payment, previous_month)

        old_debt = models.Debt.objects.create(
            branch=self.branch,
            created_by=self.phone_seller,
            f_name="Old Debt",
            amount=Decimal("50.00"),
            remaining_amount=Decimal("50.00"),
            direction="WE_GAVE",
        )
        self._set_added_at(old_debt, previous_month)

        current_salary = models.Salary.objects.create(
            branch=self.branch,
            employee=self.employee,
            amount=Decimal("300.00"),
            created_by=self.owner,
        )
        old_salary = models.Salary.objects.create(
            branch=self.branch,
            employee=self.employee,
            amount=Decimal("250.00"),
            created_by=self.owner,
        )
        self._set_added_at(old_salary, previous_month)

        explicit_request = self.factory.get("/api/", {"year": "2026", "month": "2"})
        explicit_filtered = get_filtered_queryset(
            models.Payment.objects.filter(pk__in=[current_payment.pk, previous_payment.pk]),
            explicit_request,
        )
        self.assertEqual(list(explicit_filtered.values_list("id", flat=True)), [previous_payment.id])

        default_request = self.factory.get("/api/")
        debt_ids = set(
            get_filtered_queryset(
                models.Debt.objects.filter(pk__in=[self.debt.pk, old_debt.pk]),
                default_request,
            ).values_list("id", flat=True)
        )
        salary_ids = set(
            get_filtered_queryset(
                models.Salary.objects.filter(pk__in=[current_salary.pk, old_salary.pk]),
                default_request,
            ).values_list("id", flat=True)
        )

        self.assertEqual(
            set(
                get_filtered_queryset(
                    models.Payment.objects.filter(pk__in=[current_payment.pk, previous_payment.pk]),
                    default_request,
                ).values_list("id", flat=True)
            ),
            {current_payment.id, previous_payment.id},
        )
        self.assertEqual(debt_ids, {self.debt.id, old_debt.id})
        self.assertEqual(salary_ids, {current_salary.id, old_salary.id})

    def test_pagination_returns_standard_metadata(self):
        pagination = StandardPagination()
        request = Request(self.factory.get("/api/", {"page": "2"}))

        page_items = pagination.paginate_queryset(list(range(45)), request)
        payload = pagination.get_paginated_data(page_items)

        self.assertEqual(len(page_items), 20)
        self.assertEqual(payload["count"], 45)
        self.assertIn("page=3", payload["next"])
        self.assertEqual(payload["previous"], "http://testserver/api/")
        self.assertEqual(payload["results"][0], 20)

    def test_response_helpers_and_base_api_view_use_standard_format(self):
        success_payload = self._decode(success_response({"foo": "bar"}))
        error_payload = self._decode(error_response("Bad request", status=422))

        self.assertEqual(success_payload, {"success": True, "data": {"foo": "bar"}, "error": None})
        self.assertEqual(
            error_payload,
            {"success": False, "data": {}, "error": "Bad request"},
        )

        success_request = self.factory.get("/api/")
        broken_request = self.factory.get("/api/")
        force_authenticate(success_request, user=self.owner)
        force_authenticate(broken_request, user=self.owner)

        success_view_response = SampleAPIView.as_view()(success_request)
        broken_view_response = BrokenAPIView.as_view()(broken_request)

        self.assertEqual(success_view_response.status_code, 200)
        self.assertEqual(self._decode(success_view_response)["data"]["message"], "ok")
        self.assertEqual(broken_view_response.status_code, 400)
        self.assertEqual(self._decode(broken_view_response)["error"], "bad input")

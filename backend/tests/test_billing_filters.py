from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from src.core import models


class BillingFilterViewTests(TestCase):
    def setUp(self):
        self.cashier = models.User.objects.create_user(
            username="cashier_user",
            password="pass123",
            is_cashier=True,
        )
        self.customer = models.User.objects.create_user(
            username="customer_user",
            password="pass123",
        )
        self.client.force_login(self.cashier)

    def _set_added_at(self, instance, value):
        instance.__class__.all_objects.filter(pk=instance.pk).update(
            added_at=value,
            updated_at=value,
        )
        instance.refresh_from_db()

    def test_payment_list_filters_by_year_and_month(self):
        march_payment = models.Payment.objects.create(
            user=self.customer,
            amount=Decimal("100.00"),
            payment_type="cash",
            added_by=self.cashier,
        )
        april_payment = models.Payment.objects.create(
            user=self.customer,
            amount=Decimal("200.00"),
            payment_type="cash",
            added_by=self.cashier,
        )

        self._set_added_at(
            march_payment,
            timezone.make_aware(datetime(2026, 3, 20, 10, 0, 0)),
        )
        self._set_added_at(
            april_payment,
            timezone.make_aware(datetime(2026, 4, 5, 10, 0, 0)),
        )

        response = self.client.get(
            reverse("cashier_payment_list"),
            {"year": "2026", "month": "4"},
        )

        self.assertEqual(response.status_code, 200)
        object_ids = {obj.id for obj in response.context["object_list"]}
        self.assertIn(april_payment.id, object_ids)
        self.assertNotIn(march_payment.id, object_ids)

    def test_transaction_log_list_filters_by_year_and_month(self):
        march_log = models.TransactionLog.objects.create(
            user=self.customer,
            type="payment",
            amount=Decimal("50.00"),
            charge_date=timezone.make_aware(datetime(2026, 3, 25, 9, 0, 0)),
            balance_before=Decimal("0.00"),
            balance_after=Decimal("50.00"),
        )
        april_log = models.TransactionLog.objects.create(
            user=self.customer,
            type="payment",
            amount=Decimal("75.00"),
            charge_date=timezone.make_aware(datetime(2026, 4, 2, 9, 0, 0)),
            balance_before=Decimal("50.00"),
            balance_after=Decimal("125.00"),
        )

        response = self.client.get(
            reverse("cashier_transaction_list"),
            {"year": "2026", "month": "4"},
        )

        self.assertEqual(response.status_code, 200)
        object_ids = {obj.id for obj in response.context["object_list"]}
        self.assertIn(april_log.id, object_ids)
        self.assertNotIn(march_log.id, object_ids)

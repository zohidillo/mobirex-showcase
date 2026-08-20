from types import SimpleNamespace

from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse

from src.bases.context_processors import role_flags
from src.core import models
from src.shared.navigation import (
    get_back_url,
    get_main_page_url,
    should_show_back_button,
)


class BackNavigationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.owner = models.User.objects.create_user(username="nav_owner", password="pass123")
        self.phone_seller = models.User.objects.create_user(
            username="nav_phone_seller",
            password="pass123",
        )
        self.accessory_seller = models.User.objects.create_user(
            username="nav_accessory_seller",
            password="pass123",
        )
        self.multi_role_user = models.User.objects.create_user(
            username="nav_multi_role",
            password="pass123",
        )
        self.cashier = models.User.objects.create_user(
            username="nav_cashier",
            password="pass123",
            is_cashier=True,
        )
        self.superuser = models.User.objects.create_superuser(
            username="nav_admin",
            password="pass123",
        )
        self.outsider = models.User.objects.create_user(
            username="nav_outsider",
            password="pass123",
        )

        self.branch = models.Branch.objects.create(name="Nav Branch", owner=self.owner)

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
        models.BranchUser.objects.create(
            user=self.multi_role_user,
            branch=self.branch,
            role=models.BranchUser.ROLE_OWNER,
        )
        models.BranchUser.objects.create(
            user=self.multi_role_user,
            branch=self.branch,
            role=models.BranchUser.ROLE_PHONE_SELLER,
        )
        models.BranchUser.objects.create(
            user=self.multi_role_user,
            branch=self.branch,
            role=models.BranchUser.ROLE_ACCESSORY_SELLER,
        )

    def _build_request(self, url_name, user):
        return self._build_request_with_args(url_name, user)

    def test_get_main_page_url_respects_role_priority(self):
        self.assertEqual(get_main_page_url(self.phone_seller), reverse("phone_unsold_list"))
        self.assertEqual(get_main_page_url(self.accessory_seller), reverse("accessory_unsold_list"))
        self.assertEqual(get_main_page_url(self.owner), reverse("owner-branches"))
        self.assertEqual(get_main_page_url(self.multi_role_user), reverse("phone_unsold_list"))
        self.assertEqual(get_main_page_url(self.outsider), reverse("dashboard"))

    def test_phone_dashboard_returns_unsold_phone_list(self):
        request = self._build_request("seller-dashboard", self.phone_seller)

        self.assertEqual(get_back_url(request), reverse("phone_unsold_list"))
        self.assertTrue(should_show_back_button(request))

    def test_accessory_dashboard_returns_unsold_accessory_list(self):
        request = self._build_request("accessory-seller-dashboard", self.accessory_seller)

        self.assertEqual(get_back_url(request), reverse("accessory_unsold_list"))
        self.assertTrue(should_show_back_button(request))

    def test_sold_product_pages_return_to_unsold_lists(self):
        phone_request = self._build_request("phone_sold_list", self.phone_seller)
        accessory_request = self._build_request("accessory_sold_list", self.accessory_seller)

        self.assertEqual(get_back_url(phone_request), reverse("phone_unsold_list"))
        self.assertEqual(get_back_url(accessory_request), reverse("accessory_unsold_list"))
        self.assertTrue(should_show_back_button(phone_request))
        self.assertTrue(should_show_back_button(accessory_request))

    def test_debt_list_returns_to_main_role_page(self):
        request = self._build_request("debt_list", self.phone_seller)

        self.assertEqual(get_back_url(request), reverse("phone_unsold_list"))
        self.assertTrue(should_show_back_button(request))

    def test_debt_child_pages_return_to_debt_list(self):
        for url_name in (
            "debt_paid_list",
            "debt_create",
            "debt_delete",
            "debt_payment_list",
            "debt_payment_create",
            "debt_payment_delete",
        ):
            with self.subTest(url_name=url_name):
                request = self._build_request(url_name, self.phone_seller)
                self.assertEqual(get_back_url(request), reverse("debt_list"))
                self.assertTrue(should_show_back_button(request))

    def test_general_list_pages_return_to_main_role_page(self):
        for url_name in (
            "phone_unsold_list",
            "accessory_unsold_list",
            "expense_list",
            "salary_list",
            "my_salary_list",
            "extra_profit_list",
            "journal_list",
            "phone_capital_list",
            "accessory_capital_list",
            "owner-branches",
            "owner-branch-employees",
            "owner-employee-dashboard",
            "owner-branch-accessory-dashboard",
            "profile_account",
            "profile_change_password",
        ):
            user = self.owner
            if url_name in {"phone_unsold_list"}:
                user = self.phone_seller
            elif url_name in {"accessory_unsold_list"}:
                user = self.accessory_seller

            request = self._build_request_with_args(url_name, user)
            self.assertEqual(get_back_url(request), get_main_page_url(user))
            self.assertTrue(should_show_back_button(request))

    def test_multi_role_user_uses_phone_priority_outside_special_cases(self):
        request = self._build_request("phone_create", self.multi_role_user)

        self.assertEqual(get_back_url(request), reverse("phone_unsold_list"))
        self.assertTrue(should_show_back_button(request))

    def test_multi_role_user_still_uses_debt_override(self):
        request = self._build_request("debt_payment_create", self.multi_role_user)

        self.assertEqual(get_back_url(request), reverse("debt_list"))
        self.assertTrue(should_show_back_button(request))

    def test_cashier_and_superuser_do_not_get_back_button(self):
        cashier_request = self._build_request("cashier_payment_list", self.cashier)
        superuser_request = self._build_request("admin_user_list", self.superuser)

        self.assertFalse(should_show_back_button(cashier_request))
        self.assertFalse(should_show_back_button(superuser_request))

        cashier_payload = role_flags(cashier_request)
        superuser_payload = role_flags(superuser_request)
        self.assertEqual(cashier_payload["back_url"], "")
        self.assertEqual(superuser_payload["back_url"], "")

    def test_hidden_utility_view_does_not_show_back_button(self):
        request = self._build_request("debt_payment_debt_options", self.phone_seller)

        self.assertFalse(should_show_back_button(request))

    def test_context_processor_exposes_back_url_for_global_list_page(self):
        request = self._build_request("journal_list", self.owner)

        payload = role_flags(request)

        self.assertTrue(payload["show_back_button"])
        self.assertEqual(payload["back_url"], reverse("owner-branches"))

    def test_explicit_context_can_override_back_target(self):
        request = self._build_request("phone_create", self.phone_seller)

        self.assertEqual(
            get_back_url(request, context={"back_view_name": "debt_list"}),
            reverse("debt_list"),
        )
        self.assertTrue(should_show_back_button(request, context={"show_back_button": True}))

    def test_helper_handles_requests_without_named_routes(self):
        request = self.factory.get("/custom/")
        request.user = self.phone_seller
        request.resolver_match = SimpleNamespace(url_name=None)

        self.assertEqual(get_back_url(request), reverse("phone_unsold_list"))
        self.assertFalse(should_show_back_button(request))

    def test_rendered_list_page_contains_back_button_for_seller(self):
        self.client.force_login(self.phone_seller)

        response = self.client.get(reverse("phone_unsold_list"))

        self.assertContains(response, "Orqaga")

    def test_rendered_cashier_page_hides_back_button(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("cashier_payment_list"))

        self.assertNotContains(response, "Orqaga")

    def _build_request_with_args(self, url_name, user):
        kwargs = {}
        if url_name in {"owner-branch-employees", "owner-branch-accessory-dashboard"}:
            kwargs["branch_id"] = self.branch.id
        if url_name == "owner-employee-dashboard":
            kwargs["branch_id"] = self.branch.id
            kwargs["employee_id"] = self.phone_seller.id
        if url_name == "debt_delete":
            debt = models.Debt.objects.create(
                branch=self.branch,
                created_by=self.phone_seller,
                amount=100,
                remaining_amount=100,
                direction="WE_GAVE",
                domain=models.Debt.DOMAIN_PHONE,
            )
            kwargs["pk"] = debt.pk
        if url_name == "debt_payment_delete":
            debt = models.Debt.objects.create(
                branch=self.branch,
                created_by=self.phone_seller,
                amount=100,
                remaining_amount=50,
                direction="WE_GAVE",
                domain=models.Debt.DOMAIN_PHONE,
            )
            payment = models.DebtPayment.objects.create(
                debt=debt,
                amount=50,
                paid_by=self.phone_seller,
            )
            kwargs["pk"] = payment.pk

        path = reverse(url_name, kwargs=kwargs or None)
        request = self.factory.get(path)
        request.user = user
        request.resolver_match = resolve(path)
        return request

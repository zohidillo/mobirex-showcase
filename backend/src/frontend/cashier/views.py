from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.frontend.cashier import forms as cashier_forms
from src.services.billing import PaymentApplyService
from src.shared.filters import (
    apply_datetime_range,
    filter_by_month,
    get_request_year_month,
    parse_date_input,
)


class CashierDashboardView(LoginRequiredMixin, CashierRequiredMixin, View):
    template_name = "cashier/dashboard.html"

    def get(self, request, *args, **kwargs):
        data = DashboardService.get_cashier_dashboard()
        return render(request, self.template_name, {"data": data})


class PaymentListView(LoginRequiredMixin, CashierRequiredMixin, View):
    template_name = "cashier/payment_list.html"
    paginate_by = 20

    def get_queryset(self, request):
        queryset = (
            models.Payment.objects.filter(is_deleted=False)
            .select_related("user", "added_by")
            .only(
                "id",
                "user_id",
                "added_by_id",
                "amount",
                "payment_type",
                "added_at",
                "user__username",
                "added_by__username",
            )
            .order_by("-added_at")
        )

        user_id = request.GET.get("user")
        payment_type = request.GET.get("payment_type")
        from_date = parse_date_input(request.GET.get("from_date"))
        to_date = parse_date_input(request.GET.get("to_date"))

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        queryset = filter_by_month(
            queryset,
            request,
            field_name="added_at",
        )

        return apply_datetime_range(
            queryset,
            field_name="added_at",
            from_date=from_date,
            to_date=to_date,
        )

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request)
        year, month = get_request_year_month(
            request,
            default_to_current=False,
            source=request.path,
        )
        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {
            "page_obj": page_obj,
            "object_list": page_obj.object_list,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "users": models.User.objects.filter(is_deleted=False).only("id", "username").order_by(
                "username"
            ),
            "payment_types": models.Payment._meta.get_field("payment_type").choices,
            "filters": {
                "user": request.GET.get("user", ""),
                "payment_type": request.GET.get("payment_type", ""),
                "year": str(year or ""),
                "month": str(month or ""),
                "from_date": request.GET.get("from_date", ""),
                "to_date": request.GET.get("to_date", ""),
            },
        }
        return render(request, self.template_name, context)


class PaymentCreateView(LoginRequiredMixin, CashierRequiredMixin, View):
    template_name = "cashier/payment_create.html"

    def get_initial(self, request):
        initial = {}
        user_id = request.GET.get("user")
        if user_id:
            initial["user"] = user_id
        return initial

    def get(self, request, *args, **kwargs):
        form = cashier_forms.PaymentForm(initial=self.get_initial(request))
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = cashier_forms.PaymentForm(request.POST)
        if form.is_valid():
            try:
                PaymentApplyService.create_payment(
                    user=form.cleaned_data["user"],
                    amount=form.cleaned_data["amount"],
                    payment_type=form.cleaned_data["payment_type"],
                    added_by=request.user,
                )
                messages.success(request, _("To‘lov muvaffaqiyatli qo‘shildi."))
                return redirect(reverse("cashier_payment_list"))
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
        return render(request, self.template_name, {"form": form})


class TransactionLogListView(LoginRequiredMixin, CashierRequiredMixin, View):
    template_name = "cashier/transaction_list.html"
    paginate_by = 20

    def get_queryset(self, request):
        queryset = (
            models.TransactionLog.objects.filter(is_deleted=False)
            .select_related("user")
            .only(
                "id",
                "user_id",
                "type",
                "amount",
                "charge_date",
                "balance_before",
                "balance_after",
                "user__username",
            )
            .order_by("-charge_date", "-id")
        )

        user_id = request.GET.get("user")
        transaction_type = request.GET.get("type")
        from_date = parse_date_input(request.GET.get("from_date"))
        to_date = parse_date_input(request.GET.get("to_date"))

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        queryset = filter_by_month(
            queryset,
            request,
            field_name="charge_date",
        )

        return apply_datetime_range(
            queryset,
            field_name="charge_date",
            from_date=from_date,
            to_date=to_date,
        )

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request)
        year, month = get_request_year_month(
            request,
            default_to_current=False,
            source=request.path,
        )
        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {
            "page_obj": page_obj,
            "object_list": page_obj.object_list,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "users": models.User.objects.filter(is_deleted=False).only("id", "username").order_by(
                "username"
            ),
            "transaction_types": models.TransactionLog._meta.get_field("type").choices,
            "filters": {
                "user": request.GET.get("user", ""),
                "type": request.GET.get("type", ""),
                "year": str(year or ""),
                "month": str(month or ""),
                "from_date": request.GET.get("from_date", ""),
                "to_date": request.GET.get("to_date", ""),
            },
        }
        return render(request, self.template_name, context)


class LegacyPaymentMutationView(LoginRequiredMixin, CashierRequiredMixin, View):
    message = _("Eski tahrirlash yoki o‘chirish oqimi o‘rniga yangi to‘lov qo‘shing.")

    def get(self, request, *args, **kwargs):
        messages.info(request, self.message)
        return redirect(reverse("cashier_payment_list"))

    post = get


SubscriptionPaymentListView = PaymentListView
SubscriptionPaymentCreateView = PaymentCreateView
SubscriptionPaymentUpdateView = LegacyPaymentMutationView
SubscriptionPaymentDeleteView = LegacyPaymentMutationView

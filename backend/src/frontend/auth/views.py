from django import forms
from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from django.views import View
from django.utils.translation import gettext_lazy as _

from src.core.models import TransactionLog
from src.services.billing import AccountAccessService
from src.shared.filters import (
    apply_datetime_range,
    filter_by_month,
    get_request_year_month,
    parse_date_input,
)


class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": _("Login yoki parol noto‘g‘ri."),
        "inactive": _("Hisob faol emas."),
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if getattr(user, "is_deleted", False):
            raise ValidationError(_("Hisob o‘chirilgan."))
        decision = AccountAccessService.evaluate_user(user, persist=True)
        self.account_access_decision = decision
        if not decision.is_allowed:
            raise ValidationError(decision.blocked_message)


class CustomLoginView(DjangoLoginView):
    template_name = "auth/login.html"
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def _reverse_first(self, *names):
        for name in names:
            try:
                return reverse(name)
            except NoReverseMatch:
                continue
        return "/"

    def get_success_url(self):
        user = self.request.user
        if user.has_role("PHONE_SELLER"):
            return reverse("phone_unsold_list")
        if user.has_role("ACCESSORY_SELLER"):
            return reverse("accessory_unsold_list")
        if user.has_role("OWNER"):
            return reverse("owner-branches")
        if user.is_cashier:
            return self._reverse_first("cashier_dashboard", "cashier-dashboard")
        if user.is_superuser:
            return self._reverse_first("admin_dashboard", "admin-dashboard")
        return reverse("dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        decision = getattr(form, "account_access_decision", None)
        if decision is None:
            decision = AccountAccessService.evaluate_user(self.request.user, persist=True)
        if not decision.is_allowed:
            logout(self.request)
            messages.error(self.request, decision.blocked_message)
            return redirect(reverse("login"))
        if decision.warning_message:
            messages.warning(self.request, decision.warning_message)
        return response

    def form_invalid(self, form):
        errors = form.non_field_errors()
        if errors:
            messages.error(self.request, errors.as_text().replace("* ", "").strip())
        else:
            messages.error(self.request, _("Login yoki parol noto‘g‘ri."))
        return super().form_invalid(form)


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse("login"))


class UserPasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label=_("Eski parol"),
        widget=forms.PasswordInput,
    )
    new_password = forms.CharField(
        label=_("Yangi parol"),
        widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        label=_("Parolni tasdiqlang"),
        widget=forms.PasswordInput,
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned = super().clean()
        old_password = cleaned.get("old_password")
        new_password = cleaned.get("new_password")
        confirm_password = cleaned.get("confirm_password")
        if old_password and not self.user.check_password(old_password):
            raise ValidationError(_("Eski parol noto‘g‘ri."))
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError(_("Parollar mos emas."))
        return cleaned


class UserPasswordChangeView(LoginRequiredMixin, View):
    template_name = "profile/change_password.html"

    def get(self, request, *args, **kwargs):
        form = UserPasswordChangeForm(user=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    new_password = form.cleaned_data["new_password"]
                    request.user.set_password(new_password)
                    request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, _("Parol muvaffaqiyatli yangilandi."))
                return redirect(reverse("profile_change_password"))
            except Exception as exc:
                messages.error(request, str(exc))
        return render(request, self.template_name, {"form": form})


class ProfileAccountView(LoginRequiredMixin, View):
    template_name = "profile/account.html"
    paginate_by = 20

    def get_queryset(self, request):
        queryset = (
            TransactionLog.objects.filter(is_deleted=False, user=request.user)
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

        transaction_type = request.GET.get("type")
        from_date = parse_date_input(request.GET.get("from_date"))
        to_date = parse_date_input(request.GET.get("to_date"))

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
            "transaction_types": TransactionLog._meta.get_field("type").choices,
            "filters": {
                "type": request.GET.get("type", ""),
                "year": str(year or ""),
                "month": str(month or ""),
                "from_date": request.GET.get("from_date", ""),
                "to_date": request.GET.get("to_date", ""),
            },
        }
        return render(request, self.template_name, context)

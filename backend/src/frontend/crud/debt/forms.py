from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _

import src.core.models as models
from src.services.debt import filter_debts_for_month
from src.shared.permissions import get_primary_seller_branch, get_seller_domain_for_branch


class DebtCreateForm(forms.ModelForm):
    branch = forms.ModelChoiceField(
        queryset=models.Branch.objects.none(),
        required=False,
        label=_("Filial"),
        empty_label=_("Filialni tanlang"),
        widget=forms.Select(
            attrs={
                "class": "tom-select w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 min-h-[44px] text-gray-100",
            }
        ),
    )
    direction = forms.ChoiceField(
        choices=models.Debt._meta.get_field("direction").choices,
        label=_("Qarz yo‘nalishi"),
    )

    class Meta:
        model = models.Debt
        fields = [
            "f_name",
            "amount",
            "direction",
            "note",
        ]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        selected_branch = kwargs.pop("branch", None)
        super().__init__(*args, **kwargs)
        if not user:
            return

        if user.has_role("ACCESSORY_SELLER"):
            self.fields.pop("branch", None)
            return

        if user.has_role("OWNER"):
            branches = user.get_all_branches("OWNER")
            if not branches:
                branches = list(models.Branch.objects.filter(owner=user))
            branch_ids = [b.id for b in branches if b]
            if branch_ids:
                self.fields["branch"].queryset = models.Branch.objects.filter(id__in=branch_ids)
                self.fields["branch"].required = True
            else:
                self.fields["branch"].queryset = models.Branch.objects.none()
            if self.data.get("branch"):
                try:
                    selected_branch_id = int(self.data.get("branch"))
                except (TypeError, ValueError):
                    selected_branch_id = None
                if selected_branch_id is not None and selected_branch_id not in branch_ids:
                    selected_branch_id = None
            elif selected_branch and selected_branch.id in branch_ids:
                self.fields["branch"].initial = selected_branch
        else:
            self.fields.pop("branch", None)

    def clean_amount(self):
        value = self.cleaned_data.get("amount")
        if value is None:
            raise ValidationError(_("Summani kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri summa."))
        if value <= 0:
            raise ValidationError(_("Summa noldan katta bo‘lishi kerak."))
        return value

    def clean_direction(self):
        value = self.cleaned_data.get("direction")
        if not value:
            raise ValidationError(_("Yo‘nalishni tanlash shart."))
        return value


class DebtUpdateForm(forms.ModelForm):
    direction = forms.ChoiceField(
        choices=models.Debt._meta.get_field("direction").choices,
        label=_("Qarz yo‘nalishi"),
    )

    class Meta:
        model = models.Debt
        fields = [
            "f_name",
            "amount",
            "direction",
            "note",
        ]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["direction"].initial = self.instance.direction
            self.fields["direction"].disabled = True

    def clean_amount(self):
        value = self.cleaned_data.get("amount")
        if value is None:
            raise ValidationError(_("Summani kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri summa."))
        if value <= 0:
            raise ValidationError(_("Summa noldan katta bo‘lishi kerak."))
        return value

    def clean_direction(self):
        value = self.cleaned_data.get("direction")
        if self.instance and self.instance.pk:
            return self.instance.direction
        if not value:
            raise ValidationError(_("Yo‘nalishni tanlash shart."))
        return value


class DebtPaymentForm(forms.ModelForm):
    branch = forms.ModelChoiceField(
        queryset=models.Branch.objects.none(),
        required=False,
        label=_("Filial"),
        empty_label=_("Filialni tanlang"),
    )

    class Meta:
        model = models.DebtPayment
        fields = [
            "debt",
            "amount",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        selected_branch = kwargs.pop("branch", None)
        super().__init__(*args, **kwargs)
        self.fields["debt"].label_from_instance = lambda obj: (
            _("Qarz: %(name)s | %(amount)s | Qoldiq: %(remaining)s")
            % {
                "name": obj.f_name or _("Noma'lum"),
                "amount": obj.amount,
                "remaining": obj.remaining_amount,
            }
        )
        if self.instance and self.instance.pk:
            self.fields.pop("branch", None)
            self.fields["debt"].initial = self.instance.debt
            self.fields["debt"].queryset = models.Debt.objects.filter(
                pk=self.instance.debt_id
            ).select_related("branch", "created_by")
            self.fields["debt"].disabled = True
            return

        if user:
            if user.has_role("OWNER"):
                branches = user.get_all_branches("OWNER")
                branch_ids = [b.id for b in branches if b]
                if branch_ids:
                    self.fields["branch"].queryset = models.Branch.objects.filter(id__in=branch_ids)
                    self.fields["branch"].required = True
                else:
                    self.fields["branch"].queryset = models.Branch.objects.none()

                selected_branch_id = None
                if self.data.get("branch"):
                    try:
                        selected_branch_id = int(self.data.get("branch"))
                    except (TypeError, ValueError):
                        selected_branch_id = None
                elif selected_branch:
                    selected_branch_id = selected_branch.id
                    self.fields["branch"].initial = selected_branch

                if selected_branch_id is not None and selected_branch_id not in branch_ids:
                    selected_branch_id = None

                if selected_branch_id:
                    debt_qs = (
                        models.Debt.objects.filter(
                            branch_id=selected_branch_id,
                            remaining_amount__gt=0,
                            is_deleted=False,
                        )
                        .select_related("branch", "created_by")
                    )
                    self.fields["debt"].queryset = filter_debts_for_month(
                        debt_qs,
                        default_to_current=True,
                    )
                else:
                    self.fields["debt"].queryset = models.Debt.objects.none()
            elif user.has_role("PHONE_SELLER") or user.has_role("ACCESSORY_SELLER"):
                self.fields.pop("branch", None)
                branch = get_primary_seller_branch(user)
                if branch:
                    seller_domain = get_seller_domain_for_branch(user, branch)
                    debt_qs = models.Debt.objects.filter(
                        branch=branch,
                        remaining_amount__gt=0,
                        is_deleted=False,
                    )
                    if seller_domain == models.Debt.DOMAIN_ACCESSORY:
                        debt_qs = debt_qs.filter(domain=models.Debt.DOMAIN_ACCESSORY)
                    elif seller_domain == models.Debt.DOMAIN_PHONE:
                        debt_qs = debt_qs.filter(Q(domain=seller_domain) | Q(domain__isnull=True))
                    else:
                        debt_qs = debt_qs.none()
                    debt_qs = filter_debts_for_month(
                        debt_qs.select_related("branch", "created_by"),
                        default_to_current=True,
                    )
                    self.fields["debt"].queryset = debt_qs
                else:
                    self.fields["debt"].queryset = models.Debt.objects.none()
            else:
                self.fields.pop("branch", None)
                self.fields["debt"].queryset = models.Debt.objects.none()

    def clean_amount(self):
        value = self.cleaned_data.get("amount")
        if value is None:
            raise ValidationError(_("Summani kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri summa."))
        if value <= 0:
            raise ValidationError(_("Summa noldan katta bo‘lishi kerak."))
        return value

    def clean(self):
        cleaned = super().clean()
        debt = cleaned.get("debt")
        amount = cleaned.get("amount")
        if debt and amount is not None:
            active_payments = models.DebtPayment.objects.filter(debt=debt)
            if self.instance and self.instance.pk:
                active_payments = active_payments.exclude(pk=self.instance.pk)
                actual_remaining = max(
                    (debt.amount or Decimal("0.00"))
                    - (active_payments.aggregate(total_paid=Sum("amount"))["total_paid"] or Decimal("0.00")),
                    Decimal("0.00"),
                )
                max_allowed = actual_remaining + (self.instance.amount or Decimal("0.00"))
            else:
                max_allowed = max(
                    (debt.amount or Decimal("0.00"))
                    - (active_payments.aggregate(total_paid=Sum("amount"))["total_paid"] or Decimal("0.00")),
                    Decimal("0.00"),
                )
            if amount > max_allowed:
                self.add_error("amount", _("Summa qarz qoldig‘idan oshib ketdi."))
        return cleaned

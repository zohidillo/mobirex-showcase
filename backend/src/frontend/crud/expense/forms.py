from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import src.core.models as models
from src.shared.permissions import get_owner_branches


class ExpenseForm(forms.ModelForm):
    created_for = forms.ModelChoiceField(
        queryset=models.User.objects.none(),
        required=False,
        label=_("Xodim"),
    )

    class Meta:
        model = models.Expense
        fields = [
            "branch",
            "created_for",
            "type",
            "amount",
            "note",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is None:
            return

        if user.has_role("OWNER"):
            branches = user.get_all_branches("OWNER")
            if branches:
                self.fields["branch"].queryset = models.Branch.objects.filter(
                    id__in=[b.id for b in branches]
                )
            else:
                self.fields["branch"].queryset = models.Branch.objects.filter(
                    owner=user, is_deleted=False
                )
            self.fields["created_for"].queryset = models.User.objects.filter(
                branch_roles__branch__in=branches,
                branch_roles__is_deleted=False,
            ).distinct()
        elif user.is_superuser or user.is_cashier:
            self.fields["branch"].queryset = models.Branch.objects.filter(is_deleted=False)
            self.fields["created_for"].queryset = models.User.objects.none()
        else:
            self.fields.pop("branch", None)
            self.fields.pop("created_for", None)

    def clean_amount(self):
        value = self.cleaned_data.get("amount")
        if value is None:
            raise ValidationError(_("Summani kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri summa."))
        if value <= 0:
            raise ValidationError(_("Summa noldan katta bo‘lishi kerak."))
        return value


class SalaryForm(forms.ModelForm):
    class Meta:
        model = models.Salary
        fields = [
            "employee",
            "amount",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user and user.has_role("OWNER"):
            owner_branches = get_owner_branches(user)
            self.fields["employee"].queryset = models.User.objects.filter(
                branch_roles__branch__in=owner_branches,
                branch_roles__is_deleted=False,
                is_deleted=False,
            ).distinct()
        else:
            self.fields["employee"].queryset = models.User.objects.none()

    def clean_amount(self):
        value = self.cleaned_data.get("amount")
        if value is None:
            raise ValidationError(_("Summani kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri summa."))
        if value <= 0:
            raise ValidationError(_("Summa noldan katta bo‘lishi kerak."))
        return value

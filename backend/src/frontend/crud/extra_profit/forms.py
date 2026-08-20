from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import src.core.models as models


class ExtraProfitForm(forms.ModelForm):
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

    class Meta:
        model = models.ExtraProfit
        fields = [
            "branch",
            "amount",
            "note",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not user:
            return
        if user.has_role("OWNER"):
            branches = user.get_all_branches("OWNER")
            branch_ids = [b.id for b in branches if b]
            self.fields["branch"].queryset = models.Branch.objects.filter(id__in=branch_ids)
            self.fields["branch"].required = True
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

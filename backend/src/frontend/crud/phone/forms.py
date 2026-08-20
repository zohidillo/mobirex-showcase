from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import src.core.models as models


class PhoneCreateForm(forms.ModelForm):
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
        model = models.Phone
        fields = [
            "branch",
            "name",
            "category",
            "storage",
            "color",
            "from_by",
            "imei",
            "cost_price",
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


    def clean_cost_price(self):
        value = self.cleaned_data.get("cost_price")
        if value is None:
            raise ValidationError(_("Tannarxni kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri tannarx."))
        return value


class PhoneUpdateForm(forms.ModelForm):
    class Meta:
        model = models.Phone
        fields = [
            "name",
            "category",
            "storage",
            "color",
            "from_by",
            "imei",
            "cost_price",
        ]

    def clean_imei(self):
        imei = self.cleaned_data.get("imei")
        if not self.instance:
            return imei
        if imei != self.instance.imei:
            raise ValidationError(_("IMEI ni o‘zgartirib bo‘lmaydi."))
        return imei

    def clean_cost_price(self):
        value = self.cleaned_data.get("cost_price")
        if value is None:
            raise ValidationError(_("Tannarxni kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri tannarx."))
        return value


class PhoneSellForm(forms.Form):
    sell_price = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        label=_("Sotuv narxi"),
    )

    def clean_sell_price(self):
        value = self.cleaned_data.get("sell_price")
        if value is None:
            raise ValidationError(_("Sotuv narxini kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri sotuv narxi."))
        return value

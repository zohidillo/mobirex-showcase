from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import src.core.models as models
from src.shared.permissions import get_owner_branches


class AccessoryCreateForm(forms.ModelForm):
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
        model = models.Accessory
        fields = [
            "branch",
            "name",
            "category",
            "stock",
            "unit_cost",
            "image",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not user:
            return

        if user.has_role("OWNER"):
            branches = get_owner_branches(user)
            branch_ids = [branch.id for branch in branches]
            self.fields["branch"].queryset = models.Branch.objects.filter(id__in=branch_ids)
            self.fields["branch"].required = True
        else:
            self.fields.pop("branch", None)

    def clean_stock(self):
        value = self.cleaned_data.get("stock")
        if value is None or value <= 0:
            raise ValidationError(_("Soni noldan katta bo‘lishi kerak."))
        return value

    def clean_unit_cost(self):
        value = self.cleaned_data.get("unit_cost")
        if value is None:
            raise ValidationError(_("Birlik tannarxni kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri birlik tannarx."))
        if value <= 0:
            raise ValidationError(_("Birlik tannarx noldan katta bo‘lishi kerak."))
        return value


class AccessoryUpdateForm(forms.ModelForm):
    class Meta:
        model = models.Accessory
        fields = [
            "name",
            "category",
            "stock",
            "unit_cost",
            "image",
        ]

    def clean_stock(self):
        value = self.cleaned_data.get("stock")
        if value is None or value < 0:
            raise ValidationError(_("Soni manfiy bo‘lishi mumkin emas."))
        return value

    def clean_unit_cost(self):
        value = self.cleaned_data.get("unit_cost")
        if value is None:
            raise ValidationError(_("Birlik tannarxni kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri birlik tannarx."))
        if value <= 0:
            raise ValidationError(_("Birlik tannarx noldan katta bo‘lishi kerak."))
        return value


class AccessorySellForm(forms.Form):
    accessory = forms.ModelChoiceField(
        queryset=models.Accessory.objects.none(),
        label=_("Aksessuar"),
    )
    quantity = forms.IntegerField(min_value=1, label=_("Soni"))
    total_price = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        label=_("Jami sotuv narxi"),
    )

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop("accessory_queryset", None)
        super().__init__(*args, **kwargs)
        if queryset is not None:
            self.fields["accessory"].queryset = queryset

    def clean(self):
        cleaned = super().clean()
        accessory = cleaned.get("accessory")
        quantity = cleaned.get("quantity")
        if accessory and quantity is not None:
            if quantity > accessory.stock:
                self.add_error("quantity", _("Soni mavjud qoldiqdan oshib ketdi."))
        return cleaned

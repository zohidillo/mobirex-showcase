from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import src.core.models as models


class PaymentForm(forms.ModelForm):
    class Meta:
        model = models.Payment
        fields = [
            "user",
            "amount",
            "payment_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = models.User.objects.filter(is_deleted=False).order_by("username")

    def clean_amount(self):
        value = self.cleaned_data.get("amount")
        if value is None:
            raise ValidationError(_("Summani kiritish shart."))
        if not isinstance(value, Decimal):
            raise ValidationError(_("Noto‘g‘ri summa."))
        if value <= 0:
            raise ValidationError(_("Summa noldan katta bo‘lishi kerak."))
        return value

    def clean_user(self):
        value = self.cleaned_data.get("user")
        if value is None:
            raise ValidationError(_("Foydalanuvchini tanlash shart."))
        if value.is_deleted:
            raise ValidationError(_("O‘chirilgan foydalanuvchi tanlanmaydi."))
        return value


SubscriptionPaymentForm = PaymentForm

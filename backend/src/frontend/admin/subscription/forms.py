from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import src.core.models as models


class SubscriptionForm(forms.ModelForm):
    duration_days = forms.IntegerField(min_value=1, label=_("Davomiylik (kun)"))

    class Meta:
        model = models.Subscription
        fields = [
            "user",
            "plan_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["user"].disabled = True
            self.fields["plan_type"].disabled = True

    def clean_user(self):
        value = self.cleaned_data.get("user")
        if self.instance and self.instance.pk:
            if value is None:
                return self.instance.user
            if value != self.instance.user:
                raise ValidationError(_("Foydalanuvchini o‘zgartirib bo‘lmaydi."))
        return value

    def clean_plan_type(self):
        value = self.cleaned_data.get("plan_type")
        if self.instance and self.instance.pk:
            if value is None:
                return self.instance.plan_type
            if value != self.instance.plan_type:
                raise ValidationError(_("Reja turini o‘zgartirib bo‘lmaydi."))
        return value

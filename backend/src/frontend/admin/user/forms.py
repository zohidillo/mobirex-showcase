from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import src.core.models as models


class UserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        label=_("Parol"),
        widget=forms.PasswordInput,
    )

    class Meta:
        model = models.User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "daily_fee",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_vip",
            "is_cashier",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["password"].required = False
        else:
            self.fields["password"].required = True

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not self.instance or not self.instance.pk:
            if not password:
                raise ValidationError(_("Parolni kiritish shart."))
        return password


class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "daily_fee",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_vip",
            "is_cashier",
        ]


class AdminUserPasswordChangeForm(forms.Form):
    new_password = forms.CharField(
        label=_("Yangi parol"),
        widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        label=_("Parolni tasdiqlang"),
        widget=forms.PasswordInput,
    )

    def clean(self):
        cleaned = super().clean()
        new_password = cleaned.get("new_password")
        confirm_password = cleaned.get("confirm_password")
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError(_("Parollar mos emas."))
        return cleaned

from django import forms
from django.utils.translation import gettext_lazy as _

import src.core.models as models


class AdminSupportReplyForm(forms.Form):
    message = forms.CharField(
        label=_("Javob"),
        widget=forms.Textarea(attrs={"rows": 4}),
        required=True,
    )


class AdminSupportCloseForm(forms.Form):
    new_status = forms.ChoiceField(
        label=_("Yangi holat"),
        choices=[
            (models.SupportRequest.Status.RESOLVED, _("Hal qilindi")),
            (models.SupportRequest.Status.REJECTED, _("Rad etildi")),
        ],
    )
    close_reason = forms.ChoiceField(
        label=_("Sabab"),
        choices=models.SupportRequest.CloseReason.choices,
    )
    close_reason_note = forms.CharField(
        label=_("Izoh"),
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )

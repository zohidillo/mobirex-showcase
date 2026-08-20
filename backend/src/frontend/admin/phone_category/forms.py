from django import forms

import src.core.models as models


class PhoneCategoryForm(forms.ModelForm):
    class Meta:
        model = models.PhoneCategory
        fields = ["name"]

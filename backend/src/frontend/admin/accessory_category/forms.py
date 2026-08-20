from django import forms

import src.core.models as models


class AccessoryCategoryForm(forms.ModelForm):
    class Meta:
        model = models.AccessoryCategory
        fields = ["name"]

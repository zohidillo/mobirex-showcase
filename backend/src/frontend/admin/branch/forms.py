from django import forms

import src.core.models as models


class BranchForm(forms.ModelForm):
    class Meta:
        model = models.Branch
        fields = [
            "name",
            "owner",
            "address",
            "is_active",
        ]

from django import forms

import src.core.models as models


class BranchUserForm(forms.ModelForm):
    class Meta:
        model = models.BranchUser
        fields = [
            "user",
            "branch",
            "role",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = models.User.objects.filter(is_deleted=False)
        self.fields["branch"].queryset = models.Branch.objects.filter(is_deleted=False)

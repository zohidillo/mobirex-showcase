from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from src.core.models import Branch


class BranchRoleRequiredMixin(LoginRequiredMixin):
    required_role = None

    def dispatch(self, request, *args, **kwargs):
        branch = None
        branch_id = kwargs.get("branch_id") or request.GET.get("branch")
        if branch_id:
            branch = Branch.objects.filter(id=branch_id).first()
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.has_role(self.required_role, branch):
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

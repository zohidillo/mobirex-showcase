from django.db.models import Q
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from src.bases.views import *
from src.services.debt import filter_debts_for_month
from src.shared.permissions import (
    get_primary_seller_branch,
    get_seller_domain_for_branch,
)


class DebtPaymentDebtOptionsView(LoginRequiredMixin, View):
    def has_permission(self):
        user = self.request.user
        return (
            user.has_role("OWNER")
            or user.has_role("PHONE_SELLER")
            or user.has_role("ACCESSORY_SELLER")
        )

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return JsonResponse(
                {"detail": _("Sizga bu amalni bajarish mumkin emas.")},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_branch(self):
        user = self.request.user

        if user.has_role("OWNER"):
            branch_id = self.request.GET.get("branch")
            if not branch_id:
                return None
            try:
                branch_id = int(branch_id)
            except (TypeError, ValueError):
                return None

            allowed_ids = [branch.id for branch in user.get_all_branches("OWNER") if branch]
            if branch_id not in allowed_ids:
                return None

            return models.Branch.objects.filter(id=branch_id, is_deleted=False).first()

        return get_primary_seller_branch(user)

    def get(self, request, *args, **kwargs):
        branch = self.get_branch()
        if not branch:
            return JsonResponse({"debts": []})

        debts = (
            filter_debts_for_month(
                models.Debt.objects.filter(
                    branch=branch,
                    remaining_amount__gt=0,
                    is_deleted=False,
                ),
                default_to_current=True,
            )
            .select_related("branch", "created_by")
            .order_by("-added_at")
        )
        if not request.user.has_role("OWNER"):
            seller_domain = get_seller_domain_for_branch(request.user, branch)
            if seller_domain == models.Debt.DOMAIN_ACCESSORY:
                debts = debts.filter(domain=models.Debt.DOMAIN_ACCESSORY)
            elif seller_domain == models.Debt.DOMAIN_PHONE:
                debts = debts.filter(Q(domain=seller_domain) | Q(domain__isnull=True))
            else:
                debts = debts.none()

        payload = []
        for debt in debts:
            debt_name = debt.f_name or str(_("Qo‘lda kiritilgan qarz"))
            payload.append(
                {
                    "id": debt.id,
                    "label": f"{debt_name} — {debt.remaining_amount}",
                }
            )

        return JsonResponse({"debts": payload})

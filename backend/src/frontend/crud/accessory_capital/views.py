from src.bases.views import *
from src.shared.permissions import get_owner_branches


class AccessoryCapitalListView(BaseListView):
    model = models.AccessoryCapital
    template_name = "accessory_capital/list.html"
    paginate_by = 20

    def has_permission(self):
        return self.request.user.has_role("OWNER")

    def get_queryset(self):
        user = self.request.user
        owner_branches = get_owner_branches(user)
        if not owner_branches:
            return models.AccessoryCapital.objects.none()
        return (
            models.AccessoryCapital.objects.filter(branch__in=owner_branches)
            .select_related("branch")
            .order_by("branch__name", "-month")
        )

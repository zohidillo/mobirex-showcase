from src.bases.views import *


class AccessoryUnsoldListView(BaseListView):
    model = models.Accessory
    template_name = "accessory/unsold_list.html"
    paginate_by = 20

    def has_permission(self):
        user = self.request.user
        return user.has_role("OWNER") or user.has_role("ACCESSORY_SELLER")

    def get_queryset(self):
        user = self.request.user
        queryset = models.Accessory.objects.filter(
            is_deleted=False,
            stock__gt=0,
        ).select_related(
            "branch",
            "added_by",
            "category",
        ).defer("image")

        if user.has_role("OWNER"):
            branches = user.get_all_branches("OWNER")
            branch_ids = [b.id for b in branches if b]
            if not branch_ids:
                return models.Accessory.objects.none()
            queryset = queryset.filter(branch_id__in=branch_ids)
            branch_id = self.request.GET.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)
        elif user.has_role("ACCESSORY_SELLER"):
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch:
                return models.Accessory.objects.none()
            queryset = queryset.filter(branch=branch)
        else:
            return models.Accessory.objects.none()

        q = self.request.GET.get("q")
        category = self.request.GET.get("category")

        if q:
            queryset = queryset.filter(name__icontains=q)
        if category:
            queryset = queryset.filter(category_id=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        owner_branches = []
        if user.has_role("OWNER"):
            owner_branches = user.get_all_branches("OWNER")
        context.update(
            {
                "q": self.request.GET.get("q", ""),
                "category": self.request.GET.get("category", ""),
                "branch": self.request.GET.get("branch", ""),
                "owner_branches": owner_branches,
            }
        )
        return context

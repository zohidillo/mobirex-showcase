from src.bases.views import *
from src.shared.filters import (
    MONTH_CHOICES,
    filter_by_month,
    get_available_years,
    get_default_year_month,
)


class PhoneSoldListView(BaseListView):
    model = models.Phone
    template_name = "phone/sold_list.html"
    paginate_by = 20

    def has_permission(self):
        user = self.request.user
        return user.has_role("OWNER") or user.has_role("PHONE_SELLER")

    def get_base_queryset(self):
        user = self.request.user
        queryset = (
            models.Phone.objects.filter(
                is_deleted=False,
                is_sold=True,
            )
            .select_related("branch", "category", "added_by", "sold_by")
        )

        if user.has_role("OWNER"):
            branches = user.get_all_branches("OWNER")
            branch_ids = [b.id for b in branches if b]
            if not branch_ids:
                return models.Phone.objects.none()
            queryset = queryset.filter(branch_id__in=branch_ids)
            branch_id = self.request.GET.get("branch")
            if branch_id:
                try:
                    branch_id_int = int(branch_id)
                except (TypeError, ValueError):
                    branch_id_int = None
                if branch_id_int in branch_ids:
                    queryset = queryset.filter(branch_id=branch_id_int)
        elif user.has_role("PHONE_SELLER"):
            branch = user.get_primary_branch("PHONE_SELLER")
            if not branch:
                return models.Phone.objects.none()
            queryset = queryset.filter(branch=branch)
        else:
            return models.Phone.objects.none()

        q = self.request.GET.get("q")
        imei = self.request.GET.get("imei")
        name = self.request.GET.get("name")
        storage = self.request.GET.get("storage")
        category = self.request.GET.get("category")

        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(imei__icontains=q))
        if imei:
            queryset = queryset.filter(imei__icontains=imei)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if storage:
            queryset = queryset.filter(storage=storage)
        if category:
            queryset = queryset.filter(category_id=category)

        return queryset

    def get_queryset(self):
        return filter_by_month(
            self.get_base_queryset(),
            self.request,
            field_name="sold_at",
            default_to_current=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        year, month = get_default_year_month(
            self.request,
            source=self.request.path,
        )
        owner_branches = []
        if user.has_role("OWNER"):
            owner_branches = user.get_all_branches("OWNER")
        context.update(
            {
                "q": self.request.GET.get("q", ""),
                "imei": self.request.GET.get("imei", ""),
                "name": self.request.GET.get("name", ""),
                "storage": self.request.GET.get("storage", ""),
                "category": self.request.GET.get("category", ""),
                "year": str(year or ""),
                "month": str(month or ""),
                "branch": self.request.GET.get("branch", ""),
                "owner_branches": owner_branches,
                "year_options": get_available_years(self.get_base_queryset(), "sold_at"),
                "month_choices": MONTH_CHOICES,
            }
        )
        return context

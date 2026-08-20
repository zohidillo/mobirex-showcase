from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View

from src.core.models import Journal
from src.shared.filters import (
    MONTH_CHOICES,
    filter_by_month,
    get_available_years,
    get_default_year_month,
)


class JournalListView(LoginRequiredMixin, View):
    template_name = "journal/list.html"
    paginate_by = 25

    def get_queryset(self, request):
        qs = Journal.objects.select_related("user", "branch")
        user = request.user

        if user.is_superuser:
            return qs

        if user.has_role("OWNER"):
            branches = user.get_all_branches("OWNER")
            if not branches:
                return qs.none()
            return qs.filter(branch__in=branches)

        if user.has_role("PHONE_SELLER"):
            branch = user.get_primary_branch("PHONE_SELLER")
            if not branch:
                return qs.none()
            return qs.filter(
                branch=branch,
                model_name__in=["phone", "debt", "expense", "extra_profit"],
                user=user,
            )

        if user.has_role("ACCESSORY_SELLER"):
            branch = user.get_primary_branch("ACCESSORY_SELLER")
            if not branch:
                return qs.none()
            return qs.filter(
                branch=branch,
                model_name__in=["accessory", "accessorysale", "debt", "expense"],
                user=user,
            )

        return qs.none()

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset(request)
        action = request.GET.get("action")
        model_name = request.GET.get("model_name")
        year, month = get_default_year_month(
            request,
            source=request.path,
        )

        if action:
            qs = qs.filter(action=action)
        if model_name:
            qs = qs.filter(model_name=model_name)

        filtered_years_qs = qs
        qs = filter_by_month(
            qs,
            request,
            field_name="added_at",
            default_to_current=True,
        )

        qs = qs.order_by("-added_at")
        paginator = Paginator(qs, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get("page"))

        for item in page_obj.object_list:
            data = item.new_data or item.old_data or {}
            item.object_label = (
                item.object_repr
                or data.get("name")
                or data.get("title")
                or data.get("username")
                or data.get("imei")
                or data.get("person_name")
                or "-"
            )
            item.branch_name = item.branch.name if item.branch else "-"

        model_names = list(
            qs.values_list("model_name", flat=True).distinct().order_by("model_name")
        )

        context = {
            "page_obj": page_obj,
            "object_list": page_obj.object_list,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "actions": ["CREATE", "UPDATE", "DELETE"],
            "model_names": model_names,
            "filters": {
                "action": action or "",
                "model_name": model_name or "",
                "year": str(year or ""),
                "month": str(month or ""),
            },
            "year_options": get_available_years(filtered_years_qs, "added_at"),
            "month_choices": MONTH_CHOICES,
        }
        return render(request, self.template_name, context)

from django.utils.translation import gettext_lazy as _

from src.bases.views import *


class AccessorySellView(LoginRequiredMixin, View):
    template_name = "accessory/sell.html"

    def _get_accessory(self):
        pk = self.kwargs.get("pk")
        if not pk:
            return None
        return get_object_or_404(models.Accessory, pk=pk, is_deleted=False)

    def _has_access(self, user, accessory):
        return user.has_role("ACCESSORY_SELLER", accessory.branch) or user.has_role(
            "OWNER", accessory.branch
        )

    def get_queryset(self):
        user = self.request.user
        if user.has_role("ACCESSORY_SELLER") or user.has_role("OWNER"):
            branches = []
            if user.has_role("OWNER"):
                branches.extend(user.get_all_branches("OWNER"))
            if user.has_role("ACCESSORY_SELLER"):
                branches.extend(user.get_all_branches("ACCESSORY_SELLER"))
            unique = {}
            for branch in branches:
                if branch:
                    unique[branch.id] = branch
            branches = list(unique.values())
            if not branches:
                return models.Accessory.objects.none()
            return models.Accessory.objects.filter(
                branch__in=branches,
                is_deleted=False,
                stock__gt=0,
            )
        return models.Accessory.objects.none()

    def get(self, request, *args, **kwargs):
        accessory = self._get_accessory()
        if accessory and not self._has_access(request.user, accessory):
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        if not accessory and not (
            request.user.has_role("OWNER") or request.user.has_role("ACCESSORY_SELLER")
        ):
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")

        queryset = self.get_queryset()
        if accessory:
            queryset = queryset.filter(pk=accessory.pk)
        form = forms.AccessorySellForm(
            accessory_queryset=queryset,
            initial={"accessory": accessory.pk if accessory else None},
        )
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        accessory = self._get_accessory()
        if accessory and not self._has_access(request.user, accessory):
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        if not accessory and not (
            request.user.has_role("OWNER") or request.user.has_role("ACCESSORY_SELLER")
        ):
            messages.error(request, _("Sizga bu sahifaga kirish mumkin emas."))
            return redirect("dashboard")

        queryset = self.get_queryset()
        if accessory:
            queryset = queryset.filter(pk=accessory.pk)
        form = forms.AccessorySellForm(request.POST, accessory_queryset=queryset)
        if not form.is_valid():
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
            return render(request, self.template_name, {"form": form})
        selected_accessory = form.cleaned_data["accessory"]
        if not self._has_access(request.user, selected_accessory):
            messages.error(request, _("Sizga bu amalni bajarish mumkin emas."))
            return redirect("dashboard")
        try:
            AccessorySellService.sell_accessory(
                selected_accessory,
                quantity=form.cleaned_data["quantity"],
                total_price=form.cleaned_data["total_price"],
                sold_by=request.user,
            )
            messages.success(request, _("Aksessuar muvaffaqiyatli sotildi."))
            return redirect(reverse("accessory_sold_list"))
        except Exception as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {"form": form})

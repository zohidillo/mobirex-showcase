from django.utils.translation import gettext_lazy as _

from src.bases.views import *


class BranchListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/branch/list.html"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        queryset = (
            models.Branch.objects.filter(is_deleted=False)
            .select_related("owner")
            .only("id", "name", "added_at", "owner__id", "owner__username")
        )
        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {
            "page_obj": page_obj,
            "object_list": page_obj.object_list,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
        }
        return render(request, self.template_name, context)


class BranchCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/branch/create.html"

    def get(self, request, *args, **kwargs):
        form = forms.BranchForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = forms.BranchForm(request.POST)
        if form.is_valid():
            try:
                BranchCreateService.create_branch(form.cleaned_data, created_by=request.user)
                messages.success(request, _("Filial muvaffaqiyatli yaratildi."))
                return redirect(reverse("admin_branch_list"))
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
        return render(request, self.template_name, {"form": form})


class BranchUpdateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/branch/update.html"

    def get_object(self, pk):
        return get_object_or_404(models.Branch, pk=pk, is_deleted=False)

    def get(self, request, pk, *args, **kwargs):
        branch = self.get_object(pk)
        form = forms.BranchForm(instance=branch)
        return render(request, self.template_name, {"form": form, "object": branch})

    def post(self, request, pk, *args, **kwargs):
        branch = self.get_object(pk)
        form = forms.BranchForm(request.POST, instance=branch)
        if form.is_valid():
            try:
                BranchUpdateService.update_branch(
                    branch,
                    validated_data=form.cleaned_data,
                    updated_by=request.user,
                )
                messages.success(request, _("Filial muvaffaqiyatli yangilandi."))
                return redirect(reverse("admin_branch_list"))
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
        return render(request, self.template_name, {"form": form, "object": branch})


class BranchDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/branch/delete.html"

    def get_object(self, pk):
        return get_object_or_404(models.Branch, pk=pk, is_deleted=False)

    def get(self, request, pk, *args, **kwargs):
        branch = self.get_object(pk)
        return render(request, self.template_name, {"object": branch})

    def post(self, request, pk, *args, **kwargs):
        branch = self.get_object(pk)
        try:
            BranchDeleteService.delete_branch(branch, deleted_by=request.user)
            messages.success(request, _("Filial muvaffaqiyatli o‘chirildi."))
            return redirect(reverse("admin_branch_list"))
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(reverse("admin_branch_list"))

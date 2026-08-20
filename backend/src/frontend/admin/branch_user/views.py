from django.utils.translation import gettext_lazy as _

from src.bases.views import *

from src.frontend.admin.branch_user.forms import BranchUserForm


class BranchUserListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/branch_user/list.html"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        queryset = (
            models.BranchUser.objects.filter(is_deleted=False)
            .select_related("user", "branch")
            .order_by("-added_at")
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


class BranchUserCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/branch_user/create.html"

    def get(self, request, *args, **kwargs):
        form = BranchUserForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = BranchUserForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get("user")
            branch = form.cleaned_data.get("branch")
            role = form.cleaned_data.get("role")
            try:
                existing = models.BranchUser.objects.filter(
                    user=user,
                    branch=branch,
                    role=role,
                ).first()
                if existing and existing.is_deleted:
                    existing.is_deleted = False
                    existing.save()
                else:
                    models.BranchUser.objects.create(
                        user=user,
                        branch=branch,
                        role=role,
                    )
                messages.success(request, _("Filial roli muvaffaqiyatli saqlandi."))
                return redirect(reverse("admin_branch_user_list"))
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
        return render(request, self.template_name, {"form": form})


class BranchUserUpdateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/branch_user/update.html"

    def get_object(self, pk):
        return get_object_or_404(models.BranchUser, pk=pk, is_deleted=False)

    def get(self, request, pk, *args, **kwargs):
        branch_user = self.get_object(pk)
        form = BranchUserForm(instance=branch_user)
        return render(request, self.template_name, {"form": form, "object": branch_user})

    def post(self, request, pk, *args, **kwargs):
        branch_user = self.get_object(pk)
        form = BranchUserForm(request.POST, instance=branch_user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Filial roli muvaffaqiyatli yangilandi."))
                return redirect(reverse("admin_branch_user_list"))
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
        return render(request, self.template_name, {"form": form, "object": branch_user})


class BranchUserDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/branch_user/delete.html"

    def get_object(self, pk):
        return get_object_or_404(models.BranchUser, pk=pk, is_deleted=False)

    def get(self, request, pk, *args, **kwargs):
        branch_user = self.get_object(pk)
        return render(request, self.template_name, {"object": branch_user})

    def post(self, request, pk, *args, **kwargs):
        branch_user = self.get_object(pk)
        try:
            branch_user.is_deleted = True
            branch_user.save()
            messages.success(request, _("Filial roli muvaffaqiyatli o‘chirildi."))
            return redirect(reverse("admin_branch_user_list"))
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(reverse("admin_branch_user_list"))

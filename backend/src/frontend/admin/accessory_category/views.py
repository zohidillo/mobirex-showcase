from django.utils.translation import gettext_lazy as _

from src.bases.views import *


class AccessoryCategoryListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/accessory_category/list.html"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        queryset = (
            models.AccessoryCategory.objects.filter(is_deleted=False)
            .only("id", "name", "added_at")
            .order_by("name")
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


class AccessoryCategoryCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/accessory_category/create.html"

    def get(self, request, *args, **kwargs):
        form = forms.AccessoryCategoryForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = forms.AccessoryCategoryForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, _("Kategoriya muvaffaqiyatli yaratildi."))
                return redirect(reverse("admin_accessory_category_list"))
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
        return render(request, self.template_name, {"form": form})


class AccessoryCategoryUpdateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/accessory_category/update.html"

    def get_object(self, pk):
        return get_object_or_404(models.AccessoryCategory, pk=pk, is_deleted=False)

    def get(self, request, pk, *args, **kwargs):
        category = self.get_object(pk)
        form = forms.AccessoryCategoryForm(instance=category)
        return render(request, self.template_name, {"form": form, "object": category})

    def post(self, request, pk, *args, **kwargs):
        category = self.get_object(pk)
        form = forms.AccessoryCategoryForm(request.POST, instance=category)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, _("Kategoriya muvaffaqiyatli yangilandi."))
                return redirect(reverse("admin_accessory_category_list"))
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
        return render(request, self.template_name, {"form": form, "object": category})


class AccessoryCategoryDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/accessory_category/delete.html"

    def get_object(self, pk):
        return get_object_or_404(models.AccessoryCategory, pk=pk, is_deleted=False)

    def get(self, request, pk, *args, **kwargs):
        category = self.get_object(pk)
        return render(request, self.template_name, {"object": category})

    def post(self, request, pk, *args, **kwargs):
        category = self.get_object(pk)
        try:
            with transaction.atomic():
                category.is_deleted = True
                category.save(update_fields=["is_deleted", "updated_at"])
            messages.success(request, _("Kategoriya muvaffaqiyatli o‘chirildi."))
            return redirect(reverse("admin_accessory_category_list"))
        except Exception as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {"object": category})

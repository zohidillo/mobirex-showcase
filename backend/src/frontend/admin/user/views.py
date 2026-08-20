from django.utils.translation import gettext_lazy as _

from django.db import transaction
from src.bases.views import *
from src.frontend.admin.user import forms as admin_user_forms


class UserListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/user/list.html"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        queryset = (
            models.User.objects.filter(is_deleted=False)
            .only(
                "id",
                "username",
                "first_name",
                "last_name",
                "is_cashier",
                "balance",
                "daily_fee",
                "account_status",
            )
            .order_by("username")
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


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/user/create.html"

    def get(self, request, *args, **kwargs):
        form = forms.UserForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = forms.UserForm(request.POST)
        if form.is_valid():
            try:
                UserCreateService.create_user(form.cleaned_data, created_by=request.user)
                messages.success(request, _("Foydalanuvchi muvaffaqiyatli yaratildi."))
                return redirect(reverse("admin_user_list"))
            except Exception as exc:
                print(exc)
                messages.error(request, str(exc))
        else:
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
        return render(request, self.template_name, {"form": form})


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/user/update.html"

    def get_object(self, pk):
        return get_object_or_404(models.User, pk=pk, is_deleted=False)

    def get(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        form = admin_user_forms.AdminUserUpdateForm(instance=user)
        return render(request, self.template_name, {"form": form, "object": user})

    def post(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        form = admin_user_forms.AdminUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            try:
                UserUpdateService.update_user(
                    user,
                    validated_data=form.cleaned_data,
                    updated_by=request.user,
                )
                messages.success(request, _("Foydalanuvchi muvaffaqiyatli yangilandi."))
                return redirect(reverse("admin_user_list"))
            except Exception as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
        return render(request, self.template_name, {"form": form, "object": user})


class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/user/delete.html"

    def get_object(self, pk):
        return get_object_or_404(models.User, pk=pk, is_deleted=False)

    def get(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        return render(request, self.template_name, {"object": user})

    def post(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        try:
            UserDeleteService.delete_user(user, deleted_by=request.user)
            messages.success(request, _("Foydalanuvchi muvaffaqiyatli o‘chirildi."))
            return redirect(reverse("admin_user_list"))
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect(reverse("admin_user_list"))


class AdminUserPasswordChangeView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/user/change_password.html"

    def get_object(self, pk):
        return get_object_or_404(models.User, pk=pk, is_deleted=False)

    def get(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        form = admin_user_forms.AdminUserPasswordChangeForm()
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": user,
            },
        )

    def post(self, request, pk, *args, **kwargs):
        user = self.get_object(pk)
        form = admin_user_forms.AdminUserPasswordChangeForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    new_password = form.cleaned_data["new_password"]
                    user.set_password(new_password)
                    user.save()
                messages.success(request, _("Parol muvaffaqiyatli yangilandi."))
                return redirect(reverse("admin_user_list"))
            except Exception as exc:
                messages.error(request, str(exc))
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": user,
            },
        )

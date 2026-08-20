from django.utils.translation import gettext_lazy as _

from src.bases.views import *


class SubscriptionListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/subscription/list.html"
    paginate_by = 20

    def get_queryset(self, request):
        queryset = (
            models.User.objects.filter(is_deleted=False)
            .only(
                "id",
                "username",
                "first_name",
                "last_name",
                "balance",
                "daily_fee",
                "grace_start_date",
                "account_status",
            )
            .order_by("username")
        )

        user_id = request.GET.get("user")
        status = request.GET.get("status")
        if user_id:
            queryset = queryset.filter(id=user_id)
        if status:
            queryset = queryset.filter(account_status=status)
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request)
        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {
            "page_obj": page_obj,
            "object_list": page_obj.object_list,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "users": models.User.objects.filter(is_deleted=False).only("id", "username").order_by(
                "username"
            ),
            "status_choices": models.User._meta.get_field("account_status").choices,
            "filters": {
                "user": request.GET.get("user", ""),
                "status": request.GET.get("status", ""),
            },
        }
        return render(request, self.template_name, context)


class LegacySubscriptionRedirectView(LoginRequiredMixin, AdminRequiredMixin, View):
    message = _("Eski obuna sahifasi yangi balans tizimi bilan almashtirildi.")
    target_name = "admin_account_list"

    def get(self, request, *args, **kwargs):
        messages.info(request, self.message)
        return redirect(reverse(self.target_name))

    post = get


class LegacySubscriptionCreateRedirectView(LegacySubscriptionRedirectView):
    message = _("Obuna yaratish o‘rniga foydalanuvchi balansiga to‘lov qo‘shing.")
    target_name = "cashier_payment_create"

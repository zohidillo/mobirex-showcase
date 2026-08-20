from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import View

import src.core.models as models
from src.frontend.admin.mixins import AdminRequiredMixin
from src.frontend.admin.support import forms as admin_support_forms
from src.services.support import (
    close_request,
    create_admin_reply,
    mark_admin_read,
)


class AdminSupportListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/support/list.html"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        queryset = (
            models.SupportRequest.objects.filter(is_deleted=False)
            .select_related("user", "closed_by")
            .order_by("-added_at", "-id")
        )

        source = request.GET.get("source") or ""
        request_type = request.GET.get("request_type") or ""
        status = request.GET.get("status") or ""
        q = (request.GET.get("q") or "").strip()

        if source:
            queryset = queryset.filter(source=source)
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        if status:
            queryset = queryset.filter(status=status)
        if q:
            queryset = queryset.filter(
                Q(full_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(user__username__icontains=q)
            )

        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get("page"))
        context = {
            "page_obj": page_obj,
            "object_list": page_obj.object_list,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "filter_source": source,
            "filter_request_type": request_type,
            "filter_status": status,
            "filter_q": q,
            "source_choices": models.SupportRequest.Source.choices,
            "request_type_choices": models.SupportRequest.RequestType.choices,
            "status_choices": models.SupportRequest.Status.choices,
        }
        return render(request, self.template_name, context)


class AdminSupportDetailView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "admin/support/detail.html"

    def get_object(self, pk):
        queryset = (
            models.SupportRequest.objects.filter(is_deleted=False)
            .select_related("user", "closed_by")
            .prefetch_related(
                Prefetch(
                    "messages",
                    queryset=models.SupportRequestMessage.objects.filter(is_deleted=False)
                    .select_related("sender")
                    .order_by("added_at", "id"),
                    to_attr="prefetched_messages",
                )
            )
        )
        return get_object_or_404(queryset, pk=pk)

    def get(self, request, pk, *args, **kwargs):
        support_request = self.get_object(pk)
        mark_admin_read(support_request)
        reply_form = admin_support_forms.AdminSupportReplyForm()
        close_form = admin_support_forms.AdminSupportCloseForm()
        is_closed = support_request.closed_at is not None
        is_telegram = support_request.source == models.SupportRequest.Source.TELEGRAM_BOT
        context = {
            "object": support_request,
            "messages_list": getattr(support_request, "prefetched_messages", []),
            "reply_form": reply_form,
            "close_form": close_form,
            "is_closed": is_closed,
            "is_telegram": is_telegram,
            "can_reply": not is_closed and not is_telegram,
            "can_close": not is_closed,
        }
        return render(request, self.template_name, context)


class AdminSupportReplyView(LoginRequiredMixin, AdminRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk, *args, **kwargs):
        support_request = get_object_or_404(
            models.SupportRequest.objects.filter(is_deleted=False),
            pk=pk,
        )
        if support_request.closed_at is not None:
            messages.error(request, _("Murojaat allaqachon yopilgan."))
            return redirect(reverse("admin_support_detail", args=[pk]))
        if support_request.source == models.SupportRequest.Source.TELEGRAM_BOT:
            messages.error(
                request,
                _("Telegram murojaatlariga bu yerdan javob bering: TG guruh orqali"),
            )
            return redirect(reverse("admin_support_detail", args=[pk]))

        form = admin_support_forms.AdminSupportReplyForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
            return redirect(reverse("admin_support_detail", args=[pk]))

        create_admin_reply(
            support_request,
            admin_user=request.user,
            message=form.cleaned_data["message"],
        )
        messages.success(request, _("Javob yuborildi."))
        return redirect(reverse("admin_support_detail", args=[pk]))


class AdminSupportCloseView(LoginRequiredMixin, AdminRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk, *args, **kwargs):
        support_request = get_object_or_404(
            models.SupportRequest.objects.filter(is_deleted=False),
            pk=pk,
        )
        if support_request.closed_at is not None:
            messages.error(request, _("Murojaat allaqachon yopilgan."))
            return redirect(reverse("admin_support_detail", args=[pk]))

        form = admin_support_forms.AdminSupportCloseForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Iltimos, xatolarni to‘g‘rilang."))
            return redirect(reverse("admin_support_detail", args=[pk]))

        try:
            close_request(
                request_obj=support_request,
                closed_by=request.user,
                close_reason=form.cleaned_data["close_reason"],
                close_reason_note=form.cleaned_data.get("close_reason_note", ""),
                new_status=form.cleaned_data["new_status"],
            )
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect(reverse("admin_support_detail", args=[pk]))

        messages.success(request, _("Murojaat yopildi."))
        return redirect(reverse("admin_support_detail", args=[pk]))

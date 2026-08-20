from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View


def _dashboard_url(user):
    if user.is_superuser:
        return reverse("admin-dashboard")
    if user.is_cashier:
        return reverse("cashier-dashboard")
    if user.has_role("OWNER"):
        return reverse("owner-branches")
    if user.has_role("PHONE_SELLER"):
        return reverse("seller-dashboard")
    if user.has_role("ACCESSORY_SELLER"):
        return reverse("accessory-seller-dashboard")
    return "/"


class DashboardRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return redirect(_dashboard_url(request.user))

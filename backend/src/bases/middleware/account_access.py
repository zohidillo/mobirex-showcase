from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

from src.services.billing import AccountAccessService


class AccountAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, "user", None) and request.user.is_authenticated:
            decision = AccountAccessService.evaluate_user(request.user, persist=True)
            request.account_access_decision = decision
            request.account_warning_message = decision.warning_message

            logout_path = reverse("logout")
            if not decision.is_allowed and request.path != logout_path:
                logout(request)
                messages.error(request, decision.blocked_message)
                return redirect("login")

        return self.get_response(request)

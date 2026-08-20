"""Account API URLs."""

from django.urls import path

from src.api.views.account import AccountDeleteAPIView


urlpatterns = [
    path("account/delete/", AccountDeleteAPIView.as_view(), name="api_account_delete"),
]

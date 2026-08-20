"""Auth API URLs."""

from django.urls import path

from src.api.views.auth import (
    AuthLoginAPIView,
    ChangePinAPIView,
    PasswordChangeAPIView,
    SetPinAPIView,
    VerifyPinAPIView,
)


urlpatterns = [
    path("auth/login/", AuthLoginAPIView.as_view(), name="api_auth_login"),
    path("auth/pin/set/", SetPinAPIView.as_view(), name="api_auth_pin_set"),
    path("auth/pin/verify/", VerifyPinAPIView.as_view(), name="api_auth_pin_verify"),
    path("auth/pin/change/", ChangePinAPIView.as_view(), name="api_auth_pin_change"),
    path(
        "auth/change-password/",
        PasswordChangeAPIView.as_view(),
        name="api_auth_change_password",
    ),
]

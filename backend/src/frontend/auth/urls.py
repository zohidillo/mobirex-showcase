from django.urls import path

from src.frontend.auth.views import (
    CustomLoginView,
    LogoutView,
    ProfileAccountView,
    UserPasswordChangeView,
)

urlpatterns = [
    path("", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileAccountView.as_view(), name="profile_account"),
    path(
        "profile/change-password/",
        UserPasswordChangeView.as_view(),
        name="profile_change_password",
    ),
]

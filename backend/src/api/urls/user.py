"""User API URLs."""

from django.urls import path

from src.api.views.user import MeAPIView, MeSettingsAPIView, UserListAPIView, UserUpdateAPIView


urlpatterns = [
    path("me/", MeAPIView.as_view(), name="api_me"),
    path("me/settings/", MeSettingsAPIView.as_view(), name="api_me_settings"),
    path("users/", UserListAPIView.as_view(), name="api_user_list"),
    path("users/<int:pk>/", UserUpdateAPIView.as_view(), name="api_user_detail"),
]

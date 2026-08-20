from django.urls import path

from src.frontend.admin.user.views import (
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
    AdminUserPasswordChangeView,
)

urlpatterns = [
    path("users/", UserListView.as_view(), name="admin_user_list"),
    path("users/create/", UserCreateView.as_view(), name="admin_user_create"),
    path("users/<int:pk>/update/", UserUpdateView.as_view(), name="admin_user_update"),
    path(
        "users/<int:pk>/change-password/",
        AdminUserPasswordChangeView.as_view(),
        name="admin_user_change_password",
    ),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="admin_user_delete"),
]

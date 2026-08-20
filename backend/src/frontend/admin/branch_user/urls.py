from django.urls import path

from src.frontend.admin.branch_user.views import (
    BranchUserListView,
    BranchUserCreateView,
    BranchUserUpdateView,
    BranchUserDeleteView,
)

urlpatterns = [
    path("admin/branch-users/", BranchUserListView.as_view(), name="admin_branch_user_list"),
    path(
        "admin/branch-users/create/",
        BranchUserCreateView.as_view(),
        name="admin_branch_user_create",
    ),
    path(
        "admin/branch-users/<int:pk>/update/",
        BranchUserUpdateView.as_view(),
        name="admin_branch_user_update",
    ),
    path(
        "admin/branch-users/<int:pk>/delete/",
        BranchUserDeleteView.as_view(),
        name="admin_branch_user_delete",
    ),
]

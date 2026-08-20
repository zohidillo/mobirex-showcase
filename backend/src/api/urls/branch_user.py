"""Branch-user API URLs."""

from django.urls import path

from src.api.views.branch_user import (
    BranchUserCreateAPIView,
    BranchUserListAPIView,
    BranchUserUpdateAPIView,
)


class BranchUserListCreateAPIView(BranchUserListAPIView, BranchUserCreateAPIView):
    """List or create branch role assignments."""


urlpatterns = [
    path(
        "branch-users/",
        BranchUserListCreateAPIView.as_view(),
        name="api_branch_user_list_create",
    ),
    path(
        "branch-users/<int:pk>/",
        BranchUserUpdateAPIView.as_view(),
        name="api_branch_user_detail",
    ),
]

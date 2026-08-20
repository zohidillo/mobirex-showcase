"""Branch API URLs."""

from django.urls import path

from src.api.views.branch import BranchCreateAPIView, BranchListAPIView, BranchUpdateAPIView


class BranchListCreateAPIView(BranchListAPIView, BranchCreateAPIView):
    """List or create branches with admin rules."""


urlpatterns = [
    path("branches/", BranchListCreateAPIView.as_view(), name="api_branch_list_create"),
    path("branches/<int:pk>/", BranchUpdateAPIView.as_view(), name="api_branch_detail"),
]

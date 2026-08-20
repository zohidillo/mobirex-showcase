from django.urls import path

from src.frontend.admin.branch.views import (
    BranchListView,
    BranchCreateView,
    BranchUpdateView,
    BranchDeleteView,
)

urlpatterns = [
    path("branches/", BranchListView.as_view(), name="admin_branch_list"),
    path("branches/create/", BranchCreateView.as_view(), name="admin_branch_create"),
    path("branches/<int:pk>/update/", BranchUpdateView.as_view(), name="admin_branch_update"),
    path("branches/<int:pk>/delete/", BranchDeleteView.as_view(), name="admin_branch_delete"),
]

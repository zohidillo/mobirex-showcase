from django.urls import path

from src.frontend.admin.support.views import (
    AdminSupportCloseView,
    AdminSupportDetailView,
    AdminSupportListView,
    AdminSupportReplyView,
)


urlpatterns = [
    path("support/", AdminSupportListView.as_view(), name="admin_support_list"),
    path("support/<int:pk>/", AdminSupportDetailView.as_view(), name="admin_support_detail"),
    path("support/<int:pk>/reply/", AdminSupportReplyView.as_view(), name="admin_support_reply"),
    path("support/<int:pk>/close/", AdminSupportCloseView.as_view(), name="admin_support_close"),
]

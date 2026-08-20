from django.urls import path

from src.api.views.support import (
    SupportRequestDetailAPIView,
    SupportRequestListCreateAPIView,
    SupportRequestMessageCreateAPIView,
)


urlpatterns = [
    path(
        "support/requests/",
        SupportRequestListCreateAPIView.as_view(),
        name="api_support_request_list_create",
    ),
    path(
        "support/requests/<int:pk>/",
        SupportRequestDetailAPIView.as_view(),
        name="api_support_request_detail",
    ),
    path(
        "support/requests/<int:pk>/messages/",
        SupportRequestMessageCreateAPIView.as_view(),
        name="api_support_request_message_create",
    ),
]

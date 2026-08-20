"""Extra profit API URLs."""

from django.urls import path

from src.api.views.extra_profit import (
    ExtraProfitCreateAPIView,
    ExtraProfitDeleteAPIView,
    ExtraProfitListAPIView,
)


class ExtraProfitListCreateAPIView(ExtraProfitListAPIView, ExtraProfitCreateAPIView):
    """List or create extra profit with shared API rules."""


urlpatterns = [
    path(
        "extra-profit/",
        ExtraProfitListCreateAPIView.as_view(),
        name="api_extra_profit_list_create",
    ),
    path(
        "extra-profit/<int:pk>/",
        ExtraProfitDeleteAPIView.as_view(),
        name="api_extra_profit_delete",
    ),
]

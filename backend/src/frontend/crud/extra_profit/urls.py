from django.urls import path

from src.frontend.crud.extra_profit.views import (
    ExtraProfitListView,
    ExtraProfitCreateView,
    ExtraProfitDeleteView,
)

urlpatterns = [
    path("extra-profit/list/", ExtraProfitListView.as_view(), name="extra_profit_list"),
    path("extra-profit/create/", ExtraProfitCreateView.as_view(), name="extra_profit_create"),
    path("extra-profit/<int:pk>/delete/", ExtraProfitDeleteView.as_view(), name="extra_profit_delete"),
]

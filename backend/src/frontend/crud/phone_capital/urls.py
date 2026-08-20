from django.urls import path

from src.frontend.crud.phone_capital.views import (
    PhoneCapitalListView,
    PhoneCapitalCreateView,
    PhoneCapitalResetView,
)

urlpatterns = [
    path("phone-capital/", PhoneCapitalListView.as_view(), name="phone_capital_list"),
    path("phone-capital/create/", PhoneCapitalCreateView.as_view(), name="phone_capital_create"),
    path(
        "phone-capital/<int:pk>/reset/",
        PhoneCapitalResetView.as_view(),
        name="phone_capital_reset",
    ),
]

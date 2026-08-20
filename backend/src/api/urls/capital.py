"""Capital API URLs."""

from django.urls import path

from src.api.views.capital import (
    AccessoryCapitalAPIView,
    PhoneCapitalAPIView,
    PhoneCapitalResetAPIView,
)


urlpatterns = [
    path("capital/phone/", PhoneCapitalAPIView.as_view(), name="api_phone_capital_list"),
    path(
        "capital/phone/reset/",
        PhoneCapitalResetAPIView.as_view(),
        name="api_phone_capital_reset",
    ),
    path(
        "capital/accessory/",
        AccessoryCapitalAPIView.as_view(),
        name="api_accessory_capital_list",
    ),
]

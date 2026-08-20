from django.urls import path

from src.frontend.crud.accessory_capital.views import AccessoryCapitalListView

urlpatterns = [
    path(
        "accessory-capital/",
        AccessoryCapitalListView.as_view(),
        name="accessory_capital_list",
    ),
]

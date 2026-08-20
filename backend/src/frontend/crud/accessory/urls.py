from django.urls import path

from src.frontend.crud.accessory.views import (
    AccessoryUnsoldListView,
    AccessorySoldListView,
    AccessoryCreateView,
    AccessoryDeleteView,
    AccessorySellView,
    AccessoryReturnView,
)

urlpatterns = [
    path("accessory/", AccessoryUnsoldListView.as_view(), name="accessory_unsold_list"),
    path(
        "accessory/unsold/",
        AccessoryUnsoldListView.as_view(),
        name="accessory_unsold_list_legacy",
    ),
    path("accessory/sold/", AccessorySoldListView.as_view(), name="accessory_sold_list"),
    path("accessory/create/", AccessoryCreateView.as_view(), name="accessory_create"),
    path("accessory/<int:pk>/delete/", AccessoryDeleteView.as_view(), name="accessory_delete"),
    path("accessory/<int:pk>/sell/", AccessorySellView.as_view(), name="accessory_sell"),
    path(
        "accessory/sale/<int:pk>/return/",
        AccessoryReturnView.as_view(),
        name="accessory_return",
    ),
    path("accessory/sell/", AccessorySellView.as_view(), name="accessory_sell_select"),
]

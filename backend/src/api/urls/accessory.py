from django.urls import path

from src.api.views.accessory import (
    AccessoryCreateAPIView,
    AccessoryDeleteAPIView,
    AccessoryEmployeeListAPIView,
    AccessoryReturnAPIView,
    AccessorySellAPIView,
    AccessorySoldListAPIView,
    AccessoryUnsoldListAPIView,
)


urlpatterns = [
    path(
        "accessories/unsold/",
        AccessoryUnsoldListAPIView.as_view(),
        name="api_accessory_unsold_list",
    ),
    path(
        "accessories/sold/",
        AccessorySoldListAPIView.as_view(),
        name="api_accessory_sold_list",
    ),
    path(
        "accessories/employees/",
        AccessoryEmployeeListAPIView.as_view(),
        name="api_accessory_employee_list",
    ),
    path("accessories/", AccessoryCreateAPIView.as_view(), name="api_accessory_create"),
    path(
        "accessories/<int:pk>/sell/",
        AccessorySellAPIView.as_view(),
        name="api_accessory_sell",
    ),
    path(
        "accessories/sales/<int:pk>/return/",
        AccessoryReturnAPIView.as_view(),
        name="api_accessory_return",
    ),
    path(
        "accessories/<int:pk>/",
        AccessoryDeleteAPIView.as_view(),
        name="api_accessory_delete",
    ),
]

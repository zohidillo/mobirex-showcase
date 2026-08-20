"""Category API URLs."""

from django.urls import path

from src.api.views.category import AccessoryCategoryListAPIView, PhoneCategoryListAPIView


urlpatterns = [
    path("categories/phone/", PhoneCategoryListAPIView.as_view(), name="api_phone_category_list"),
    path(
        "categories/accessory/",
        AccessoryCategoryListAPIView.as_view(),
        name="api_accessory_category_list",
    ),
]

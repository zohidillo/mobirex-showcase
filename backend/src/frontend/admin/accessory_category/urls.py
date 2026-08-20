from django.urls import path

from src.frontend.admin.accessory_category.views import (
    AccessoryCategoryListView,
    AccessoryCategoryCreateView,
    AccessoryCategoryUpdateView,
    AccessoryCategoryDeleteView,
)

urlpatterns = [
    path("admin/accessory-categories/", AccessoryCategoryListView.as_view(), name="admin_accessory_category_list"),
    path("admin/accessory-categories/create/", AccessoryCategoryCreateView.as_view(), name="admin_accessory_category_create"),
    path("admin/accessory-categories/<int:pk>/update/", AccessoryCategoryUpdateView.as_view(), name="admin_accessory_category_update"),
    path("admin/accessory-categories/<int:pk>/delete/", AccessoryCategoryDeleteView.as_view(), name="admin_accessory_category_delete"),
]

from django.urls import path

from src.frontend.admin.phone_category.views import (
    PhoneCategoryListView,
    PhoneCategoryCreateView,
    PhoneCategoryUpdateView,
    PhoneCategoryDeleteView,
)

urlpatterns = [
    path("admin/phone-categories/", PhoneCategoryListView.as_view(), name="admin_phone_category_list"),
    path("admin/phone-categories/create/", PhoneCategoryCreateView.as_view(), name="admin_phone_category_create"),
    path("admin/phone-categories/<int:pk>/update/", PhoneCategoryUpdateView.as_view(), name="admin_phone_category_update"),
    path("admin/phone-categories/<int:pk>/delete/", PhoneCategoryDeleteView.as_view(), name="admin_phone_category_delete"),
]

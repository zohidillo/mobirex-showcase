from django.urls import path

from src.frontend.crud.phone.views import (
    PhoneUnsoldListView,
    PhoneSoldListView,
    PhoneCreateView,
    PhoneDeleteView,
    PhoneSellView,
    PhoneReturnView,
)

urlpatterns = [
    path("phone/unsold/", PhoneUnsoldListView.as_view(), name="phone_unsold_list"),
    path("phone/sold/", PhoneSoldListView.as_view(), name="phone_sold_list"),
    path("phone/create/", PhoneCreateView.as_view(), name="phone_create"),
    path("phone/<int:pk>/delete/", PhoneDeleteView.as_view(), name="phone_delete"),
    path("phone/<int:pk>/sell/", PhoneSellView.as_view(), name="phone_sell"),
    path("phone/<int:pk>/return/", PhoneReturnView.as_view(), name="phone_return"),
]

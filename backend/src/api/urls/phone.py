from django.urls import path

from src.api.views.phone.views import (
    PhoneCreateAPIView,
    PhoneDeleteAPIView,
    PhoneReturnAPIView,
    PhoneSellAPIView,
    PhoneSoldListAPIView,
    PhoneUnsoldListAPIView,
)

urlpatterns = [
    path("phones/unsold/", PhoneUnsoldListAPIView.as_view(), name="api_phone_unsold_list"),
    path("phones/sold/", PhoneSoldListAPIView.as_view(), name="api_phone_sold_list"),
    path("phones/", PhoneCreateAPIView.as_view(), name="api_phone_create"),
    path("phones/<int:pk>/sell/", PhoneSellAPIView.as_view(), name="api_phone_sell"),
    path("phones/<int:pk>/return/", PhoneReturnAPIView.as_view(), name="api_phone_return"),
    path("phones/<int:pk>/", PhoneDeleteAPIView.as_view(), name="api_phone_delete"),
]

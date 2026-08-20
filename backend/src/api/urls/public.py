from django.urls import path

from src.api.views.public import PublicContactRequestAPIView, RegionListAPIView


urlpatterns = [
    path(
        "public/contact-request/",
        PublicContactRequestAPIView.as_view(),
        name="api_public_contact_request",
    ),
    path(
        "regions/",
        RegionListAPIView.as_view(),
        name="api_region_list",
    ),
]

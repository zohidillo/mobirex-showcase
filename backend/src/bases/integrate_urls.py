from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("", include("src.bases.main_urls")),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
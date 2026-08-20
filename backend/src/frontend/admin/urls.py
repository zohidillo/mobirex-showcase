from django.urls import include, path

urlpatterns = [
    path("", include("src.frontend.admin.branch.urls")),
    path("", include("src.frontend.admin.user.urls")),
    path("", include("src.frontend.admin.subscription.urls")),
    path("", include("src.frontend.admin.support.urls")),
]

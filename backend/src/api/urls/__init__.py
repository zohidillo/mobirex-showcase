from django.urls import include, path


urlpatterns = [
    path("", include("src.api.urls.auth")),
    path("", include("src.api.urls.dashboard")),
    path("", include("src.api.urls.phone")),
    path("", include("src.api.urls.accessory")),
    path("", include("src.api.urls.debt")),
    path("", include("src.api.urls.expense")),
    path("", include("src.api.urls.salary")),
    path("", include("src.api.urls.extra_profit")),
    path("", include("src.api.urls.capital")),
    path("", include("src.api.urls.journal")),
    path("", include("src.api.urls.category")),
    path("", include("src.api.urls.user")),
    path("", include("src.api.urls.branch")),
    path("", include("src.api.urls.branch_user")),
    path("", include("src.api.urls.billing")),
    path("", include("src.api.urls.me")),
    path("", include("src.api.urls.support")),
    path("", include("src.api.urls.error_reporting")),
    path("", include("src.api.urls.account")),
    path("", include("src.api.urls.public")),
]

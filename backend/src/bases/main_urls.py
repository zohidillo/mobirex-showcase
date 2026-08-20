from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[IsAdminUser]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[IsAdminUser]), name="swagger-ui"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include("src.api.urls")),
    path("", include("src.frontend.dashboards.urls")),
    path("", include("src.frontend.auth.urls")),
    path("admin/", include("src.frontend.admin.urls")),
    path("", include("src.frontend.admin.phone_category.urls")),
    path("", include("src.frontend.admin.accessory_category.urls")),
    path("", include("src.frontend.admin.branch_user.urls")),
    path("", include("src.frontend.cashier.urls")),
    path("", include("src.frontend.journal.urls")),
    path("", include("src.frontend.crud.phone.urls")),
    path("", include("src.frontend.crud.accessory.urls")),
    path("", include("src.frontend.crud.debt.urls")),
    path("", include("src.frontend.crud.expense.urls")),
    path("", include("src.frontend.crud.extra_profit.urls")),
    path("", include("src.frontend.crud.phone_capital.urls")),
    path("", include("src.frontend.crud.accessory_capital.urls")),
]

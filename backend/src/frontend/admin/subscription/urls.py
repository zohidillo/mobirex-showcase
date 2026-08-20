from django.urls import path

from src.frontend.admin.subscription.views import (
    SubscriptionListView,
    LegacySubscriptionCreateRedirectView,
    LegacySubscriptionRedirectView,
)

urlpatterns = [
    path("accounts/", SubscriptionListView.as_view(), name="admin_account_list"),
    path("subscriptions/", LegacySubscriptionRedirectView.as_view(), name="admin_subscription_list"),
    path(
        "subscriptions/create/",
        LegacySubscriptionCreateRedirectView.as_view(),
        name="admin_subscription_create",
    ),
    path(
        "subscriptions/<int:pk>/update/",
        LegacySubscriptionRedirectView.as_view(),
        name="admin_subscription_update",
    ),
    path(
        "subscriptions/<int:pk>/delete/",
        LegacySubscriptionRedirectView.as_view(),
        name="admin_subscription_delete",
    ),
]

"""Journal API URLs."""

from django.urls import path

from src.api.views.journal import JournalListAPIView


urlpatterns = [
    path("journal/", JournalListAPIView.as_view(), name="api_journal_list"),
]

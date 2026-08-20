from django.urls import path

from src.frontend.journal.views import JournalListView

urlpatterns = [
    path("journal/", JournalListView.as_view(), name="journal_list"),
]

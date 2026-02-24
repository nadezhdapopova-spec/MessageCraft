from django.urls import path

from mailings.views import (
    MailingCreateView,
    MailingDeleteView,
    MailingDetailView,
    MailingListView,
    MailingPreviewView,
    MailingUpdateView,
    mailing_search_view,
)

app_name = "mailings"

urlpatterns = [
    path("mailings", MailingListView.as_view(), name="mailings_list"),
    path("search/", mailing_search_view, name="mailing_search"),
    path("mailing/<int:pk>/", MailingDetailView.as_view(), name="mailing_detail"),
    path("create/", MailingCreateView.as_view(), name="mailing_create"),
    path("mailing/<int:pk>/update/", MailingUpdateView.as_view(), name="mailing_update"),
    path("<int:pk>/preview/", MailingPreviewView.as_view(), name="mailing_preview"),
    path("mailing/<int:pk>/delete/", MailingDeleteView.as_view(), name="mailing_delete"),
]

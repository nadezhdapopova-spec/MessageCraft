from django.urls import path

from reports.views import DashboardView, CampaignReportView, ContactsView

app_name = "reports"

urlpatterns = [
    path("home/", DashboardView.as_view(), name="home"),
    path("campaigns/", CampaignReportView.as_view(), name="campaign_report"),
    path("contacts/", ContactsView.as_view(), name="contacts"),
]

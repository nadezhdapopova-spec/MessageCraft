from django.urls import path

from reports.views import CampaignReportView, ContactsView, DashboardView, UserDashboardView, export_campaigns_csv

app_name = "reports"

urlpatterns = [
    path("home/", DashboardView.as_view(), name="home"),
    path("user_dashboard/", UserDashboardView.as_view(), name="user_dashboard"),
    path("campaigns/", CampaignReportView.as_view(), name="campaign_report"),
    path("campaigns/export/", export_campaigns_csv, name="export_campaigns_csv"),
    path("contacts/", ContactsView.as_view(), name="contacts"),
]

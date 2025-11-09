from django.urls import path

from reports.views import CampaignReportView, ContactsView, DashboardView, UserDashboardView

app_name = "reports"

urlpatterns = [
    path("home/", DashboardView.as_view(), name="home"),
    path("user_dashboard/", UserDashboardView.as_view(), name="user_dashboard"),
    path("campaigns/", CampaignReportView.as_view(), name="campaign_report"),
    path("contacts/", ContactsView.as_view(), name="contacts"),
]

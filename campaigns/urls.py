from django.urls import path

from campaigns.views import CampaignListView, CampaignCreateView, CampaignUpdateView, CampaignDeleteView, \
    CampaignDetailView, CampaignSendView, campaign_search_view

app_name = "campaigns"

urlpatterns = [
    path("campaigns/", CampaignListView.as_view(), name="campaigns_list"),
    path("create/", CampaignCreateView.as_view(), name="campaign_create"),
    path("campaign/<int:pk>/update/", CampaignUpdateView.as_view(), name="campaign_update"),
    path("campaign/<int:pk>/delete/", CampaignDeleteView.as_view(), name="campaign_delete"),
    path("campaign/<int:pk>/", CampaignDetailView.as_view(), name="campaign_detail"),
    path("campaign/<int:pk>/send/", CampaignSendView.as_view(), name="campaign_send"),
    path("search/", campaign_search_view, name="campaign_search"),
]

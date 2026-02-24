from django.urls import path

from management_panel.views import (
    CampaignsManagementView,
    UsersManagementView,
    block_users,
    enable_campaigns,
    stop_campaigns,
    unblock_users,
)

app_name = "management_panel"

urlpatterns = [
    path("users/", UsersManagementView.as_view(), name="users_management"),
    path("campaigns/", CampaignsManagementView.as_view(), name="campaigns_management"),
    path("users/block/", block_users, name="block_users"),
    path("users/unblock/", unblock_users, name="unblock_users"),
    path("campaigns/stop/", stop_campaigns, name="stop_campaigns"),
    path("campaigns/enable/", enable_campaigns, name="enable_campaigns"),
]

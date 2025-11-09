from django.db.models import Count, Q

from campaigns.models import Attempt, Campaign
from clients.models import Client


def get_dashboard_stats():
    return {
        "total_campaigns": Campaign.objects.count(),
        "active_campaigns": Campaign.objects.filter(status="RUNNING").count(),
        "unique_clients": Client.objects.values("email").distinct().count(),
        "successful_attempts": Attempt.objects.filter(status="SUCCESS").count(),
        "failed_attempts": Attempt.objects.filter(status="FAIL").count(),
    }


def get_campaign_reports():
    return (
        Campaign.objects.annotate(
            total_attempts=Count("attempts"),
            success_count=Count("attempts", filter=Q(attempts__status="SUCCESS")),
            fail_count=Count("attempts", filter=Q(attempts__status="FAIL")),
        )
        .select_related("owner")
        .order_by("-created_at")
    )

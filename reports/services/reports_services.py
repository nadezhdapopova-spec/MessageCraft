from django.db.models import Count, Q

from campaigns.models import Attempt, Campaign
from clients.models import Client


def get_dashboard_stats():
    """
    Возвращает статистику по рассылкам: всего рассылок, активных рассылок, уникальных клиентов,
    успешных/неуспешных рассылок
    """
    return {
        "total_campaigns": Campaign.objects.count(),
        "active_campaigns": Campaign.objects.filter(status="RUNNING").count(),
        "unique_clients": Client.objects.values("email").distinct().count(),
        "successful_attempts": Attempt.objects.filter(status="SUCCESS").count(),
        "failed_attempts": Attempt.objects.filter(status="FAIL").count(),
    }


def get_campaign_reports():
    """Возвращает статистику по попыткам рассылок: всего попыток рассылок, успешных/неуспешных попыток рассылок"""
    return (
        Campaign.objects.annotate(
            total_attempts=Count("attempts"),
            success_count=Count("attempts", filter=Q(attempts__status="SUCCESS")),
            fail_count=Count("attempts", filter=Q(attempts__status="FAIL")),
        )
        .select_related("owner")
        .order_by("-created_at")
    )


def get_campaign_report_queryset(request):
    """Общий метод для получения отчётного queryset по рассылкам"""
    user = request.user
    status_filter = request.GET.get("status")

    qs = Campaign.objects.annotate(
        total_attempts=Count("attempts"),
        success_count=Count("attempts", filter=Q(attempts__status="SUCCESS")),
        fail_count=Count("attempts", filter=Q(attempts__status="FAIL")),
    ).select_related("owner")

    if not user.is_staff:
        qs = qs.filter(owner=user)
        qs = qs.order_by("-created_at")
    else:
        qs = qs.order_by("owner__username", "-created_at", "name")

    if status_filter:
        qs = qs.filter(status=status_filter)

    return qs

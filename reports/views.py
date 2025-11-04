from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from campaigns.models import Campaign
from clients.models import Client
from attempts.models import Attempt
from django.views.generic import TemplateView, ListView


class DashboardView(LoginRequiredMixin, TemplateView):
    """Главная страница (дашборд): общая статистика по сервису"""
    template_name = "reports/home.html"


def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)

    context["total_campaigns"] = Campaign.objects.count()
    context["active_campaigns"] = Campaign.objects.filter(status="RUNNING").count()
    context["unique_clients"] = Client.objects.values("email").distinct().count()

    context["total_attempts"] = Attempt.objects.count()
    context["successful_attempts"] = Attempt.objects.filter(status="SUCCESS").count()
    context["failed_attempts"] = Attempt.objects.filter(status="FAIL").count()

    return context


class CampaignReportView(LoginRequiredMixin, ListView):
    """Страница отчётов по рассылкам:количество попыток, процент успеха, владелец"""
    model = Campaign
    template_name = "reports/campaign_report.html"
    context_object_name = "reports"
    paginate_by = 10
    login_url = "users:login"


    def get_queryset(self):
        user = self.request.user
        status_filter = self.request.GET.get("status")

        qs = (Campaign.objects.annotate(total_attempts=Count("attempts"),
                                          success_count=Count("attempts", filter=Q(attempts__status="SUCCESS")),
                                          fail_count=Count("attempts", filter=Q(attempts__status="FAIL")),
                                          )
                .select_related("owner").order_by("-created_at"))

        if not user.is_staff:
            qs = qs.filter(owner=user)

        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "")
        context["statuses"] = Campaign.STATUS_CHOICES
        return context

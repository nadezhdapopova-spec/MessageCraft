from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, TemplateView

from campaigns.models import Attempt, Campaign
from clients.models import Client
from reports.forms import FeedbackForm
from reports.models import Contacts


class DashboardView(TemplateView):
    """Главная страница (дашборд): общая статистика по сервису"""

    template_name = "reports/home.html"

    def get_context_data(self, **kwargs):
        """
        Добавляет общую статистику в контекст:
        всего рассылок, активных рассылок, уникальных клиентов,
        всего попыток рассылок, успешных/неуспешных попыток рассылок
        """
        context = super().get_context_data(**kwargs)

        context["total_campaigns"] = Campaign.objects.count()
        context["active_campaigns"] = Campaign.objects.filter(status="RUNNING").count()
        context["unique_clients"] = Client.objects.values("email").distinct().count()

        context["total_attempts"] = Attempt.objects.count()
        context["successful_attempts"] = Attempt.objects.filter(status="SUCCESS").count()
        context["failed_attempts"] = Attempt.objects.filter(status="FAIL").count()

        return context


class UserDashboardView(LoginRequiredMixin, TemplateView):
    """Персональная статистика пользователя"""

    template_name = "reports/user_dashboard.html"

    def get_context_data(self, **kwargs):
        """
        Добавляет статистику пользователя в контекст:
        всего рассылок, активных рассылок, уникальных клиентов,
        всего попыток рассылок, успешных/неуспешных попыток рассылок
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["total_campaigns"] = Campaign.objects.filter(owner=user).count()
        context["active_campaigns"] = Campaign.objects.filter(owner=user, status="RUNNING").count()
        context["unique_clients"] = Client.objects.filter(owner=user).values("email").distinct().count()
        context["total_attempts"] = Attempt.objects.filter(campaign__owner=user).count()
        context["successful_attempts"] = Attempt.objects.filter(campaign__owner=user, status="SUCCESS").count()
        context["failed_attempts"] = Attempt.objects.filter(campaign__owner=user, status="FAIL").count()

        return context


class CampaignReportView(LoginRequiredMixin, ListView):
    """Страница отчётов по рассылкам:количество попыток, процент успеха, владелец"""

    template_name = "reports/campaign_report.html"
    context_object_name = "reports"
    paginate_by = 10
    login_url = "users:login"

    def get_queryset(self):
        """
        Возвращает список отчетов о рассылках в зависимости от прав пользователя:
        пользователю - отчеты о своих рассылках, менеджеру и суперпользователю - все.
        Добавляет возможность фильтрации по статусу рассылки
        """
        user = self.request.user
        status_filter = self.request.GET.get("status")

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

    def get_context_data(self, **kwargs):
        """Добавляет в контекст статус рассылки"""
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "")
        context["statuses"] = Campaign.STATUS_CHOICES
        return context


class ContactsView(FormView):
    """Представление для страницы Контакты"""

    form_class = FeedbackForm
    template_name = "reports/contacts.html"
    success_url = reverse_lazy("reports:contacts")

    def get_context_data(self, **kwargs):
        """Добавляет последнюю сохраненную контактную информацию в контекст"""
        context = super().get_context_data(**kwargs)
        context["contacts"] = Contacts.objects.last()
        return context

    def form_valid(self, form):
        """Сохраняет данные формы в базу данных, добавляет 'флеш-сообщение'"""
        feedback = form.save()
        messages.success(self.request, f"Спасибо, {feedback.name}! Ваше сообщение получено")
        return super().form_valid(form)

    def form_invalid(self, form):
        """
        Добавляет сообщение об ошибке, возвращает пользователя на страницу с формой и показывает ошибки валидации
        """
        messages.error(self.request, "Пожалуйста, заполните все поля")
        return super().form_invalid(form)

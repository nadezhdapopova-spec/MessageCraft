import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, ListView, TemplateView

from campaigns.models import Attempt, Campaign
from clients.models import Client
from reports.forms import FeedbackForm
from reports.models import Contacts
from reports.services.reports_services import get_campaign_report_queryset


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
        return get_campaign_report_queryset(self.request)

    def get_context_data(self, **kwargs):
        """Добавляет в контекст статус рассылки"""
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "")
        context["statuses"] = Campaign.STATUS_CHOICES
        return context


@login_required
def export_campaigns_csv(request):
    """Экспорт отчёта по рассылкам в CSV"""
    campaigns = get_campaign_report_queryset(request)

    if not campaigns.exists():
        messages.warning(request, "Нет данных для экспорта отчёта.")
        return redirect("reports:campaign_report")

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")  # cоздаётся HTTP-ответ: это CSV-файл, кодировка UTF-8 с BOM (помогает Excel корректно распознавать русские буквы)
    filename = f"campaign_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"  # campaign_report_20240215_153422.csv: уникальное имя
    response["Content-Disposition"] = f'attachment; filename="{filename}"'  # заголовок HTTP, который говорит браузеру: не показывать файл в браузере, а скачать его как вложение, установить имя файла
    response.write("\ufeff".encode("utf-8"))  # запись BOM (Byte Order Mark) в начало файла, чтобы Excel и другие программы правильно поняли кодировку UTF-8 и корректно показали кириллицу

    writer = csv.writer(response, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(
        [
            "ID",
            "Название кампании",
            "Статус",
            "Автор",
            "Дата создания",
            "Всего попыток",
            "Успешно",
            "Неудачно",
            "Процент успеха (%)",
        ]
    )

    for c in campaigns:
        success_rate = 0
        if c.total_attempts > 0:
            success_rate = round((c.success_count / c.total_attempts) * 100, 2)

        writer.writerow(
            [
                c.id,
                getattr(c, "name", "—"),
                c.get_status_display() if hasattr(c, "get_status_display") else c.status,
                c.owner.username if c.owner else "—",
                c.created_at.strftime("%d.%m.%Y %H:%M"),
                c.total_attempts,
                c.success_count,
                c.fail_count,
                success_rate,
            ]
        )

    return response


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

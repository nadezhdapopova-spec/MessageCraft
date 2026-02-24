import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from common.permissions import can_user_view, check_user_can_create, check_user_can_delete, check_user_can_edit
from common.search_utils import search_objects
from common.user_utils import get_cached_objects, invalidate_obj_cache

from .forms import CampaignForm
from .models import Campaign
from .services.campaigns_services import check_user_can_send_campaign, send_campaign

logger = logging.getLogger("campaigns")


class CampaignListView(LoginRequiredMixin, ListView):
    """Представление для отображения списка рассылок"""

    model = Campaign
    template_name = "campaigns/campaigns_list.html"
    context_object_name = "campaigns"
    paginate_by = 10

    def get_queryset(self):
        """Возвращает список рассылок с учётом прав пользователя и фильтра по статусу"""
        qs = get_cached_objects(self.request.user, self.model)

        query = self.request.GET.get("q", "").strip()
        if query:
            search_qs = search_objects(query, self.model)
            qs = qs.filter(id__in=search_qs.values_list("id", flat=True))

        status_filter = self.request.GET.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        """Добавляет поиск и фильтр по статусам в контекст"""
        context = super().get_context_data(**kwargs)
        context["search_type"] = "campaigns"
        context["statuses"] = Campaign.STATUS_CHOICES
        context["current_status"] = self.request.GET.get("status", "")
        context["query"] = self.request.GET.get("q", "")
        return context


class CampaignDetailView(LoginRequiredMixin, DetailView):
    """Представление для отображения рассылки"""

    model = Campaign
    template_name = "campaigns/campaign_detail.html"
    context_object_name = "campaign"

    def get_object(self, queryset=None):
        """Показывает рассылку, если пользователь имеет права на просмотр"""
        campaign = super().get_object(queryset)
        can_user_view(self.request.user, campaign)
        return campaign

    def get_context_data(self, **kwargs):
        """Добавляет попытки, общее количество, количество успешных и неуспешных попыток в контекст"""
        context = super().get_context_data(**kwargs)
        context["attempts"] = self.object.attempts.all().order_by("-timestamp")
        context["success_count"] = self.object.attempts.filter(status="SUCCESS").count()
        context["fail_count"] = self.object.attempts.filter(status="FAIL").count()
        context["total_attempts"] = self.object.attempts.count()
        return context


class CampaignCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания рассылок"""

    model = Campaign
    form_class = CampaignForm
    template_name = "campaigns/campaign_form.html"
    context_object_name = "campaign"
    success_url = reverse_lazy("campaigns:campaigns_list")

    def get_form_kwargs(self):
        """Передает пользователя в аргументы формы"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Определяет в контексте объект рассылки"""
        context = super().get_context_data(**kwargs)
        context["obj"] = None
        return context

    def form_valid(self, form):
        """Присваивает текущего авторизованного пользователя как автора рассылки"""
        form.instance.owner = self.request.user
        form.instance.status = "CREATED"
        response = super().form_valid(form)
        invalidate_obj_cache(self.request.user, self.model._meta.app_label)
        logger.info(f"Рассылка создана пользователем {self.request.user}")
        return response

    def dispatch(self, request, *args, **kwargs):
        """Запрещает модераторам создавать рассылки"""
        check_user_can_create(request.user)
        return super().dispatch(request, *args, **kwargs)


class CampaignUpdateView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования рассылки"""

    model = Campaign
    template_name = "campaigns/campaign_form.html"
    form_class = CampaignForm
    context_object_name = "campaign"

    def get_form_kwargs(self):
        """Добавляет пользователя в аргументы формы"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Возвращает в контекст объект рассылки"""
        context = super().get_context_data(**kwargs)
        context["obj"] = self.object
        return context

    def get_object(self, queryset=None):
        """Возвращает кэшированыый объект рассылки, если пользователь — автор или суперпользователь"""
        if not hasattr(self, "_cached_object"):
            self._cached_object = super().get_object(queryset)
            check_user_can_edit(self.request.user, self._cached_object)
        return self._cached_object

    def form_valid(self, form):
        """После успешного сохранения формы рассылки сбрасывает кэш"""
        form.instance.status = "CREATED"
        response = super().form_valid(form)
        invalidate_obj_cache(self.request.user, self.model._meta.app_label)
        logger.info(f"Рассылка {self.object.pk} обновлена пользователем {self.request.user}")
        return response

    def handle_no_permission(self):
        """Если пользователь не авторизован, перенаправляет на страницу авторизации"""
        if not self.request.user.is_authenticated:
            return redirect("users:login")
        logger.warning(
            f"Попытка редактирования рассылки {self.object.pk} пользователем без прав доступа {self.request.user}"
        )
        raise PermissionDenied("У вас нет прав для редактирования рассылки")

    def get_success_url(self):
        """При успешном редактировании возвращает на страницу просмотра рассылки"""
        return reverse_lazy("campaigns:campaign_detail", kwargs={"pk": self.object.pk})


class CampaignDeleteView(LoginRequiredMixin, DeleteView):
    """Представление для удаления рассылки"""

    model = Campaign
    template_name = "campaigns/campaign_confirm_delete.html"
    context_object_name = "campaign"
    success_url = reverse_lazy("campaigns:campaigns_list")

    def get_object(self, queryset=None):
        """Возвращает объект, если пользователь — автор или суперпользователь"""
        campaign = super().get_object(queryset)
        check_user_can_delete(self.request.user, campaign)
        return campaign

    def delete(self, request, *args, **kwargs):
        """После удаления сбрасывает кэш рассылки"""
        self.object = self.get_object()
        response = super().delete(request, *args, **kwargs)
        invalidate_obj_cache(request.user, self.model._meta.app_label)
        logger.info(f"Рассылка {self.object.pk} удалена пользователем {self.request.user}")
        return response

    def handle_no_permission(self):
        """Если пользователь не авторизован, возвращает HTTP-ответ об отстутсвии прав для удаления рассылки"""
        if not self.request.user.is_authenticated:
            return redirect("users:login")
        logger.warning(
            f"Попытка удаления рассылки {self.object.pk} пользователем без прав доступа {self.request.user}"
        )
        raise PermissionDenied("У вас нет прав для удаления рассылки")


class CampaignSendView(LoginRequiredMixin, View):
    """Представление для ручного запуска рассылки"""

    def post(self, request, pk):
        campaign = get_object_or_404(Campaign, pk=pk)
        check_user_can_send_campaign(self.request.user, campaign)

        send_campaign(campaign.id)
        messages.success(request, f"Рассылка '{campaign.name}' отправлена")
        return redirect("campaigns:campaign_detail", pk=pk)


@require_POST
@login_required
def campaign_send_multiple(request):
    """Представление для ручного запуска нескольких рассылок одновременно"""
    ids = request.POST.getlist("campaign_ids")

    if not ids:
        messages.warning(request, "Не выбрано ни одной рассылки")
        return redirect("campaigns:campaigns_list")

    campaigns = Campaign.objects.filter(pk__in=ids)

    sent_count = 0
    for campaign in campaigns:
        try:
            check_user_can_send_campaign(request.user, campaign)
            send_campaign(campaign.id)
            sent_count += 1
        except PermissionDenied:
            logger.warning(f"Попытка запуска рассылки {campaign.name} пользователем  без прав  доступа {request.user}")
            messages.warning(request, f"Вы не можете запустить рассылку '{campaign.name}'.")
        except Exception as e:
            logger.error(f"Ошибка при запуске рассылки {campaign.name}: {e}")
            messages.error(request, f"Ошибка при запуске '{campaign.name}': {e}")
    if sent_count:
        logger.info(f"Запущено {sent_count} рассылок")
        messages.success(request, f"Запущено {sent_count} рассылок")
    return redirect("campaigns:campaigns_list")


def campaign_search_view(request):
    """Осуществляет поисковый запрос рассылки"""
    query = request.GET.get("q", "").strip()
    clients = search_objects(query, Campaign)

    paginator = Paginator(clients, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "search_type": "campaigns",
        "query": query,
        "page_obj": page_obj,
    }
    return render(request, "campaigns/campaign_search.html", context)

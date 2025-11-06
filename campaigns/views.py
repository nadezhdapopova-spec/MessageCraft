from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from common.permissions import can_user_view, check_user_can_create, check_user_can_edit, check_user_can_delete
from common.search_utils import search_objects
from common.user_utils import get_cached_objects, invalidate_obj_cache
from .forms import CampaignForm
from .models import Campaign
from .services.campaigns_services import send_campaign, check_user_can_send_campaign


class CampaignListView(LoginRequiredMixin, ListView):
    """Представление для отображения списка рассылок"""
    model = Campaign
    template_name = "campaigns/campaigns_list.html"
    context_object_name = "campaigns"
    paginate_by = 20


    def get_context_data(self, **kwargs):
        """Добавляет поиск по рассылкам в контекст"""
        context = super().get_context_data(**kwargs)
        context["search_type"] = "campaigns"
        return context


    def get_queryset(self):
        """Возвращает список рассылок с учётом прав пользователя"""
        return get_cached_objects(self.request.user, self.model)


@method_decorator(cache_page(60 * 15), name="dispatch")
class CampaignDetailView(LoginRequiredMixin, DetailView):
    """Представление для отображения сообщения"""
    model = Campaign
    template_name = "campaigns/campaign_detail.html"
    context_object_name = "campaign"


    def get_object(self, queryset=None):
        """Показывает рассылку, если пользователь имеет права на просмотр"""
        campaign = super().get_object(queryset)
        can_user_view(self.request.user, campaign)
        return campaign


    def get_context_data(self, **kwargs):
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


    def get_context_data(self, **kwargs):
        """Возвращает контекст объект рассылки"""
        context = super().get_context_data(**kwargs)
        context["obj"] = self.object
        return context


    def get_object(self, queryset=None):
        """Возвращает объект только если пользователь — автор или суперпользователь"""
        if not hasattr(self, "_cached_object"):
            self._cached_object = super().get_object(queryset)
            check_user_can_edit(self.request.user, self._cached_object)
        return self._cached_object


    def form_valid(self, form):
        """После успешного сохранения формы сбрасывает кэш"""
        form.instance.status = "CREATED"
        response = super().form_valid(form)
        invalidate_obj_cache(self.request.user, self.model._meta.app_label)
        return response


    def handle_no_permission(self):
        """Если пользователь не авторизован, перенаправляет на страницу авторизации"""
        if not self.request.user.is_authenticated:
            return redirect("users:login")
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
        """Возвращает объект только если пользователь — владелец или суперпользователь"""
        campaign = super().get_object(queryset)
        check_user_can_delete(self.request.user, campaign)
        return campaign


    def delete(self, request, *args, **kwargs):
        """После удаления сбрасывает кэш рассылки"""
        self.object = self.get_object()
        response = super().delete(request, *args, **kwargs)
        invalidate_obj_cache(request.user, self.model._meta.app_label)
        return response


    def handle_no_permission(self):
        """Если пользователь не авторизован, возвращает HTTP-ответ об отстутсвии прав для удаления рассылки"""
        if not self.request.user.is_authenticated:
            return redirect("users:login")
        raise PermissionDenied("У вас нет прав для удаления рассылки")


class CampaignSendView(LoginRequiredMixin, View):
    """Представление для ручного запуска рассылки"""
    def post(self, request, pk):
        campaign = get_object_or_404(Campaign, pk=pk)
        check_user_can_send_campaign(self.request.user, campaign)

        send_campaign(campaign)
        messages.success(request, f"Рассылка '{campaign.name}' отправлена")
        return redirect("campaigns:campaign_detail", pk=pk)


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

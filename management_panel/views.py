import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.views.generic import ListView

from campaigns.models import Campaign
from common.permissions import is_manager
from users.models import CustomUser

logger = logging.getLogger("management_panel")


class ManagerRequiredMixin:
    """Миксин для проверки прав менеджера"""

    def dispatch(self, request, *args, **kwargs):
        """Проверяет, является ли пользователь менеджером"""
        if not is_manager(request.user):
            messages.error(request, "У вас нет доступа к этой странице")
            return redirect("reports:home")
        return super().dispatch(request, *args, **kwargs)


class UsersManagementView(ManagerRequiredMixin, ListView):
    """Класс для отображения менеджеру списка пользователей"""

    model = CustomUser
    template_name = "management_panel/users_table.html"
    context_object_name = "users"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        """Добавляет в контекст проверку на статус менеджера"""
        context = super().get_context_data(**kwargs)
        context["is_manager"] = self.request.user.groups.filter(name="manager").exists()
        return context


class CampaignsManagementView(ManagerRequiredMixin, ListView):
    """Класс для отображения менеджеру списка рассылок"""

    model = Campaign
    template_name = "management_panel/campaigns_table.html"
    context_object_name = "campaigns"
    paginate_by = 25


@login_required
@user_passes_test(is_manager)
def block_users(request):
    """Блокирует выбранных пользователей"""
    ids = request.POST.getlist("selected_users")
    if ids:
        users = CustomUser.objects.filter(id__in=ids)
        users.update(is_active=False)
        logger.info(f"Пользователи ({len(ids)}) заблокированы: {ids}")
        messages.success(request, f"Пользователи ({len(ids)}) заблокированы")
    return redirect("management_panel:users_management")


@login_required
@user_passes_test(is_manager)
def stop_campaigns(request):
    """Останавливает выбранные рассылки"""
    ids = request.POST.getlist("selected_campaigns")
    if ids:
        Campaign.objects.filter(id__in=ids).update(status="DISABLED")
        logger.info(f"Остановлено рассылок: {len(ids)} ({ids})")
        messages.success(request, f"Остановлено рассылок: {len(ids)}")
    return redirect("management_panel:campaigns_management")

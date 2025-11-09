from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.views.generic import ListView

from campaigns.models import Campaign
from common.permissions import is_manager
from users.models import CustomUser


class ManagerRequiredMixin:
    """Миксин для проверки прав менеджера"""

    def dispatch(self, request, *args, **kwargs):
        if not is_manager(request.user):
            messages.error(request, "У вас нет доступа к этой странице")
            return redirect("reports:home")
        return super().dispatch(request, *args, **kwargs)


class UsersManagementView(ManagerRequiredMixin, ListView):
    model = CustomUser
    template_name = "management_panel/users_table.html"
    context_object_name = "users"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_manager"] = self.request.user.groups.filter(name="manager").exists()
        return context


class CampaignsManagementView(ManagerRequiredMixin, ListView):
    model = Campaign
    template_name = "management_panel/campaigns_table.html"
    context_object_name = "campaigns"
    paginate_by = 25


@login_required
@user_passes_test(is_manager)
def block_users(request):
    ids = request.POST.getlist("selected_users")
    if ids:
        users = CustomUser.objects.filter(id__in=ids)
        users.update(is_active=False)
        messages.success(request, f"Пользователи ({len(ids)}) заблокированы")
    return redirect("management_panel:users_management")


@login_required
@user_passes_test(is_manager)
def stop_campaigns(request):
    ids = request.POST.getlist("selected_campaigns")
    if ids:
        Campaign.objects.filter(id__in=ids).update(status="DISABLED")
        messages.success(request, f"Остановлено рассылок: {len(ids)}")
    return redirect("management_panel:campaigns_management")

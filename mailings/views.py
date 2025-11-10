import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.template import Context, Template
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from common.permissions import can_user_view, check_user_can_create, check_user_can_delete, check_user_can_edit
from common.search_utils import search_objects
from common.user_utils import get_cached_objects, invalidate_obj_cache

from .forms import MailingForm
from .models import Mailing

logger = logging.getLogger("mailings")


class MailingListView(LoginRequiredMixin, ListView):
    """Представление для отображения списка сообщений"""

    model = Mailing
    template_name = "mailings/mailings_list.html"
    context_object_name = "mailings"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        """Добавляет поиск по сообщениям в контекст"""
        context = super().get_context_data(**kwargs)
        context["search_type"] = "mailings"
        context["query"] = self.request.GET.get("q", "")
        return context

    def get_queryset(self):
        """Возвращает список сообщений с учётом прав пользователя"""
        qs = get_cached_objects(self.request.user, self.model)
        query = self.request.GET.get("q", "").strip()
        if query:
            search_qs = search_objects(query, self.model)
            qs = qs.filter(id__in=search_qs.values_list("id", flat=True))
        return qs.order_by("owner", "-created_at", "subject")


class MailingDetailView(LoginRequiredMixin, DetailView):
    """Представление для отображения сообщения"""

    model = Mailing
    template_name = "mailings/mailing_detail.html"
    context_object_name = "mail"

    def get_object(self, queryset=None):
        """Показывает сообщение, если пользователь имеет права на просмотр"""
        mail = super().get_object(queryset)
        can_user_view(self.request.user, mail)
        return mail


class MailingCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания сообщения"""

    model = Mailing
    form_class = MailingForm
    template_name = "mailings/mailing_form.html"
    context_object_name = "mail"
    success_url = reverse_lazy("mailings:mailings_list")

    def get_context_data(self, **kwargs):
        """Определяет в контексте объект сообщения"""
        context = super().get_context_data(**kwargs)
        context["obj"] = None
        return context

    def form_valid(self, form):
        """Присваивает текущего авторизованного пользователя как автора сообщения"""
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        invalidate_obj_cache(self.request.user, self.model._meta.app_label)
        logger.info(f"Сообщение создано пользователем {self.request.user}")
        return response

    def dispatch(self, request, *args, **kwargs):
        """Запрещает модераторам создавать сообщения"""
        check_user_can_create(request.user, "сообщения")
        return super().dispatch(request, *args, **kwargs)


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования сообщения"""

    model = Mailing
    template_name = "mailings/mailing_form.html"
    form_class = MailingForm
    context_object_name = "mail"

    def get_context_data(self, **kwargs):
        """Возвращает контекст объект сообщения"""
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
        response = super().form_valid(form)
        invalidate_obj_cache(self.request.user, self.model._meta.app_label)
        logger.info(f"Сообщение {self.object.pk} обновлено пользователем {self.request.user}")
        return response

    def handle_no_permission(self):
        """Если пользователь не авторизован, перенаправляет на страницу авторизации"""
        if not self.request.user.is_authenticated:
            return redirect("users:login")
        logger.warning(
            f"Попытка редактирования сообщения {self.object.pk} пользователем без прав доступа {self.request.user}"
        )
        raise PermissionDenied("У вас нет прав для редактирования сообщения")

    def get_success_url(self):
        """При успешном редактировании сообщения возвращает на страницу просмотра сообщения"""
        return reverse_lazy("mailings:mailing_detail", kwargs={"pk": self.object.pk})


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    """Представление для удаления сообщения"""

    model = Mailing
    template_name = "mailings/mailing_confirm_delete.html"
    context_object_name = "mail"
    success_url = reverse_lazy("mailings:mailings_list")

    def get_object(self, queryset=None):
        """Возвращает объект только если пользователь — владелец или суперпользователь"""
        mail = super().get_object(queryset)
        check_user_can_delete(self.request.user, mail)
        return mail

    def delete(self, request, *args, **kwargs):
        """После удаления сбрасывает кэш сообщения"""
        self.object = self.get_object()
        response = super().delete(request, *args, **kwargs)
        invalidate_obj_cache(request.user, self.model._meta.app_label)
        logger.info(f"Сообщение {self.object.pk} удалено пользователем {self.request.user}")
        return response

    def handle_no_permission(self):
        """Если пользователь не авторизован, возвращает HTTP-ответ об отстутсвии прав для удаления сообщения"""
        if not self.request.user.is_authenticated:
            return redirect("users:login")
        logger.warning(
            f"Попытка удаления сообщения {self.object.pk} пользователем без прав доступа {self.request.user}"
        )
        raise PermissionDenied("У вас нет прав для удаления сообщения")


class MailingPreviewView(LoginRequiredMixin, DetailView):
    """Предпросмотр письма перед отправкой"""

    model = Mailing
    template_name = "mailings/mailing_preview.html"
    context_object_name = "mail"

    def get_object(self, queryset=None):
        """Доступ только автору или суперпользователю"""
        mail = super().get_object(queryset)
        user = self.request.user
        if not (user == mail.owner or user.is_superuser):
            raise PermissionDenied("У вас нет прав для просмотра предпросмотра этого письма")
        return mail

    def get_context_data(self, **kwargs):
        """Готовит рендер письма с подстановкой переменных"""
        context = super().get_context_data(**kwargs)
        mail = self.object

        sample_data = {
            "full_name": "Иван Иванов",
            "email": "ivan@example.com",
        }

        template = Template(mail.body)
        rendered_body = template.render(Context(sample_data))

        context["rendered_body"] = rendered_body
        return context


def mailing_search_view(request):
    """Осуществляет поисковый запрос сообщения"""
    query = request.GET.get("q", "").strip()
    clients = search_objects(query, Mailing)

    paginator = Paginator(clients, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "search_type": "mailings",
        "query": query,
        "page_obj": page_obj,
    }
    return render(request, "mailings/mailing_search.html", context)

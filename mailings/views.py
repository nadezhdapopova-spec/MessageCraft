from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.template import Template, Context
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Mailing
from .forms import MailingForm
from .services.mailings_services import get_cached_mailings, can_user_view_mail, check_user_can_create_mail, \
    invalidate_mail_cache, check_user_can_edit_mail, check_user_can_delete_mail, search_mailings


class MailingListView(LoginRequiredMixin, ListView):
    """Представление для отображения списка сообщений"""
    model = Mailing
    template_name = "mailings/mailings_list.html"
    context_object_name = "mailings"
    paginate_by = 30


    def get_context_data(self, **kwargs):
        """Добавляет поиск по сообщениям в контекст"""
        context = super().get_context_data(**kwargs)
        context["search_type"] = "mailings"
        return context


    def get_queryset(self):
        """Возвращает список сообщений с учётом прав пользователя"""
        return get_cached_mailings(self.request.user)


@method_decorator(cache_page(60 * 15), name="dispatch")
class MailingDetailView(LoginRequiredMixin, DetailView):
    """Представление для отображения сообщения"""
    model = Mailing
    template_name = "mailings/mailing_detail.html"
    context_object_name = "mail"


    def get_object(self, queryset=None):
        """Показывает сообщение, если пользователь имеет права на просмотр"""
        mail = super().get_object(queryset)
        can_user_view_mail(self.request.user, mail)
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
        invalidate_mail_cache(self.request.user)
        return response


    def dispatch(self, request, *args, **kwargs):
        """Запрещает модераторам создавать сообщения"""
        check_user_can_create_mail(request.user)
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
            check_user_can_edit_mail(self.request.user, self._cached_object)
        return self._cached_object


    def form_valid(self, form):
        """После успешного сохранения формы сбрасывает кэш"""
        response = super().form_valid(form)
        invalidate_mail_cache(self.request.user)
        return response


    def handle_no_permission(self):
        """Если пользователь не авторизован, перенаправляет на страницу авторизации"""
        if not self.request.user.is_authenticated:
            return redirect("users:login")
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
        check_user_can_delete_mail(self.request.user, mail)
        return mail


    def delete(self, request, *args, **kwargs):
        """После удаления сбрасывает кэш клиентов"""
        self.object = self.get_object()
        response = super().delete(request, *args, **kwargs)
        invalidate_mail_cache(request.user)
        return response


    def handle_no_permission(self):
        """Если пользователь не авторизован, возвращает HTTP-ответ об отстутсвии прав для удаления сообщения"""
        if not self.request.user.is_authenticated:
            return redirect("users:login")
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
    clients = search_mailings(query)

    paginator = Paginator(clients, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "search_type": "mailings",
        "query": query,
        "page_obj": page_obj,
    }
    return render(request, "mailings/mailing_search.html", context)

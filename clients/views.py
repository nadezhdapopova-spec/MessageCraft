from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from common.permissions import check_user_can_create, check_user_can_edit, check_user_can_delete, can_user_view
from common.search_utils import search_objects
from common.user_utils import get_cached_objects, invalidate_obj_cache
from .models import Client
from .forms import ClientForm


class ClientListView(LoginRequiredMixin, ListView):
    """Представление для отображения получателей рассылок"""
    model = Client
    template_name = "clients/clients_list.html"
    context_object_name = "clients"
    paginate_by = 30


    def get_context_data(self, **kwargs):
        """Добавляет поиск по получателям рассылок в контекст"""
        context = super().get_context_data(**kwargs)
        context["search_type"] = "client"
        return context


    def get_queryset(self):
        """Возвращает список получателей рассылок с учётом прав пользователя"""
        return get_cached_objects(self.request.user, self.model)


@method_decorator(cache_page(60 * 15), name="dispatch")
class ClientDetailView(LoginRequiredMixin, DetailView):
    """Представление для отображения карточки получателя рассылки"""
    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"


    def get_object(self, queryset=None):
        """Показывает карточку получателя рассылки, если пользователь имеет права на просмотр"""
        client = super().get_object(queryset)
        can_user_view(self.request.user, client)
        return client


class ClientCreateView(LoginRequiredMixin, CreateView):
    """Представление для создания карточки получателя рассылки"""
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    context_object_name = "client"
    success_url = reverse_lazy("clients:clients_list")


    def get_context_data(self, **kwargs):
        """Определяет в контексте объект получателя рассылки"""
        context = super().get_context_data(**kwargs)
        context["obj"] = None
        return context


    def form_valid(self, form):
        """Присваивает текущего авторизованного пользователя как автора карточки получателя рассылки"""
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        invalidate_obj_cache(self.request.user, self.model._meta.app_label)
        return response


    def dispatch(self, request, *args, **kwargs):
        """Запрещает модераторам создавать карточки получателей рассылки"""
        check_user_can_create(request.user, "карточки получателей рассылки")
        return super().dispatch(request, *args, **kwargs)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """Представление для редактирования карточки получателя рассылки"""
    model = Client
    template_name = "clients/client_form.html"
    form_class = ClientForm
    context_object_name = "client"


    def get_context_data(self, **kwargs):
        """Возвращает контекст объект получателя рассылки"""
        context = super().get_context_data(**kwargs)
        context["obj"] = self.object
        return context


    def get_object(self, queryset=None):
        """Возвращает объект только если пользователь — автор или суперпользователь"""
        if not hasattr(self, "_cached_object"):
            self._cached_object = super().get_object(queryset)
            check_user_can_edit(self.request.user, self._cached_object, "карточку получателя рассылки")
        return self._cached_object


    def form_valid(self, form):
        """После успешного сохранения формы сбрасывает кэш"""
        response = super().form_valid(form)
        invalidate_obj_cache(self.request.user, self.model._meta.app_label)
        return response


    def handle_no_permission(self):
        """Если пользователь не авторизован, перенаправляет на страницу авторизации"""
        if not self.request.user.is_authenticated:
            return redirect("users:login")
        raise PermissionDenied("У вас нет прав для редактирования карточки получателя рассылки")


    def get_success_url(self):
        """При успешном редактировании карточки получателя рассылки возвращает на страницу просмотра карточки"""
        return reverse_lazy("client:client_detail", kwargs={"pk": self.object.pk})


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    """Представление для удаления карточки получателя рассылки"""
    model = Client
    template_name = "clients/client_confirm_delete.html"
    context_object_name = "client"
    success_url = reverse_lazy("clients:clients_list")


    def get_object(self, queryset=None):
        """Возвращает объект только если пользователь — владелец или суперпользователь"""
        client = super().get_object(queryset)
        check_user_can_delete(self.request.user, client, "карточку получателя рассылки")
        return client


    def delete(self, request, *args, **kwargs):
        """После удаления сбрасывает кэш клиентов"""
        self.object = self.get_object()
        response = super().delete(request, *args, **kwargs)
        invalidate_obj_cache(request.user, self.model._meta.app_label)
        return response


    def handle_no_permission(self):
        """
        Если пользователь не авторизован, возвращает HTTP-ответ об отстутсвии прав
        для удаления карточки получателя рассылки
        """
        if not self.request.user.is_authenticated:
            return redirect("users:login")
        raise PermissionDenied("У вас нет прав для удаления карточки")


def client_search_view(request):
    """Осуществляет поисковый запрос получателя рассылки"""
    query = request.GET.get("q", "").strip()
    clients = search_objects(query, Client)

    paginator = Paginator(clients, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "search_type": "client",
        "query": query,
        "page_obj": page_obj,
    }
    return render(request, "clients/clients_search.html", context)

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from config.settings import BASE_DIR
from .forms import CustomUserCreationForm, UserProfileForm, UserPasswordForm
import os
from dotenv import load_dotenv

from .services.user_services import get_greeting

load_dotenv(BASE_DIR / ".env")


class RegisterView(FormView):
    """Класс регистрации пользователя"""
    template_name = "users/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("catalog:home")


    def form_valid(self, form):
        """Сохраняет данные пользователя в базу данных, осуществляет вход пользователя в систему как авторизованного"""
        user = form.save()
        login(self.request, user)
        self.send_welcome_email(user.email)
        return super().form_valid(form)


    @staticmethod
    def send_welcome_email(user_email):
        """Отправляет на почту пользователя письмо об успешной регистрации на сайте"""
        subject = "Добро пожаловать в MessageCraft"
        message = "Спасибо, что зарегистрировались в нашем сервисе!"
        from_email = os.getenv("EMAIL_HOST_USER")
        recipient_list = [user_email,]
        send_mail(subject, message, from_email, recipient_list)


class AccountView(LoginRequiredMixin, TemplateView):
    """Личный кабинет с тремя формами на одной странице"""
    template_name = "users/account.html"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["profile_form"] = kwargs.get("profile_form") or UserProfileForm(instance=user)
        context["password_form"] = kwargs.get("password_form") or UserPasswordForm(user=user)
        context["greeting"] = get_greeting()
        return context


    def post(self, request, *args, **kwargs):
        user = request.user

        if "save_profile" in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Профиль успешно обновлён")
                return redirect("users:account")
            messages.error(request, "Исправьте ошибки в форме профиля")
            return self.render_to_response(self.get_context_data(profile_form=profile_form))

        elif "change_password" in request.POST:
            password_form = UserPasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Профиль успешно обновлён")
                update_session_auth_hash(request, password_form.user)
                return redirect("users:account")
            messages.error(request, "Исправьте ошибки в форме профиля")
            return self.render_to_response(self.get_context_data(password_form=password_form))

        return self.get(request, *args, **kwargs)

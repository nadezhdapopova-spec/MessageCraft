import logging
import os

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from dotenv import load_dotenv

from config.settings import BASE_DIR

from .forms import CustomUserCreationForm, UserPasswordForm, UserProfileForm, CustomAuthenticationForm
from .services.user_services import get_greeting

load_dotenv(BASE_DIR / ".env")
logger = logging.getLogger("users")


class RegisterView(FormView):
    """Класс регистрации пользователя"""

    template_name = "users/register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("reports:home")

    def form_valid(self, form):
        """
        Сохраняет данные пользователя в базу данных,
        осуществляет вход пользователя в систему как авторизованного
        """
        user = form.save()
        login(self.request, user)
        logger.info(f"Зарегистрирован пользователь {user.email}")
        self.send_welcome_email(user)
        return super().form_valid(form)

    @staticmethod
    def send_welcome_email(user):
        """Отправляет приветственное письмо на указанный пользователем email при регистрации"""
        subject = "Добро пожаловать в MessageCraft"
        from_email = os.getenv("EMAIL_HOST_USER")
        recipient_list = [
            user.email,
        ]

        html_content = render_to_string("users/welcome_email.html", {"user": user})

        email = EmailMultiAlternatives(subject=subject, body="", from_email=from_email, to=recipient_list)
        email.attach_alternative(html_content, "text/html")
        try:
            email.send()
            logger.info(f"Отправлено письмо пользователю {user.email}")
        except Exception as e:
            logger.error(f"Ошибка при отправке письма пользователю {user.email}: {e}")


class AccountView(LoginRequiredMixin, TemplateView):
    """Личный кабинет с тремя формами на одной странице"""

    template_name = "users/account.html"

    def get_context_data(self, **kwargs):
        """Добавляет приветствие, форму для личных данных и форму для смены пароля в контекст"""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["profile_form"] = kwargs.get("profile_form") or UserProfileForm(instance=user)
        context["password_form"] = kwargs.get("password_form") or UserPasswordForm(user=user)
        context["greeting"] = get_greeting()
        return context

    def post(self, request, *args, **kwargs):
        """Обновляет данные пользователя в личном кабинете"""
        user = request.user

        if "save_profile" in request.POST:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Профиль успешно обновлён")
                logger.info(f"Профиль {user.email} успешно обновлен")
                return redirect("users:account")
            messages.error(request, "Исправьте ошибки в форме профиля")
            return self.render_to_response(self.get_context_data(profile_form=profile_form))

        elif "change_password" in request.POST:
            password_form = UserPasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Профиль успешно обновлён")
                logger.info(f"Пароль {user.email} успешно обновлен")
                update_session_auth_hash(request, password_form.user)
                return redirect("users:account")
            messages.error(request, "Исправьте ошибки в форме профиля")
            return self.render_to_response(self.get_context_data(password_form=password_form))

        return self.get(request, *args, **kwargs)


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "users/login.html"

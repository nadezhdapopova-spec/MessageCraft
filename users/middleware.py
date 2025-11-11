from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout


class BlockedUserMiddleware:
    """Разлогинивает пользователей, у которых is_active=False"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and not user.is_active:
            logout(request)
            messages.error(request,
                           "Ваш аккаунт заблокирован. Для разблокировки аккаунта просим обратиться message-craft-service@yandex.ru")
            return redirect("users:login")
        return self.get_response(request)

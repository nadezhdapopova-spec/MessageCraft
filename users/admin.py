from django.contrib import admin
from .models import CustomUser


@admin.register(CustomUser)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("email", "username", "last_login", "is_superuser", "is_staff",
                    "is_active")
    list_filter = ("date_joined", "last_login", "is_staff", "is_active", "groups")
    search_fields = ("email", "username")
    actions = ["block_selected_users",]

    @admin.action(description="Заблокировать выбранных пользователей")
    def block_selected_users(self, request, queryset):
        if not request.user.has_perm("users.can_block_users"):
            self.message_user(
                request,
                "У вас нет прав на блокировку пользователей",
                level="error"
            )
            return

        queryset.update(is_active=False)
        self.message_user(request, "Пользователи успешно заблокированы")

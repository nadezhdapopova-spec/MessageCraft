from django.contrib import admin

from .models import Campaign


@admin.register(Campaign)
class CampaignsAdmin(admin.ModelAdmin):
    list_display = ("name", "start_at", "end_at", "status", "owner", "is_active", "updated_at")
    list_filter = ("status", "owner", "is_active")
    search_fields = ("name",)
    actions = [
        "disable_campaigns",
    ]

    @admin.action(description="Отключить выбранные рассылки")
    def disable_campaigns(self, request, queryset):
        if not request.user.has_perm("campaigns.can_disable_campaigns"):
            self.message_user(request, "У вас нет прав на отключение рассылок", level="error")
            return

        queryset.update(is_active=False)
        self.message_user(request, "Рассылки успешно отключены")

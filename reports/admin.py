from django.contrib import admin

from reports.models import Contacts


@admin.register(Contacts)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ("id", "country", "address", "email",)
    search_fields = ("id", "email",)

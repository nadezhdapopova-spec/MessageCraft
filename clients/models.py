from django.db import models
from django.db.models import SET_NULL

from users.models import CustomUser


class Client(models.Model):
    """Класс получателя рассылки"""
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    comment = models.TextField(max_length=500, blank=True, null=True, verbose_name="Комментарий",)
    owner = models.ForeignKey(CustomUser,
                              on_delete=SET_NULL,
                              null=True,
                              blank=True,
                              related_name="clients",
                              verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True,
                                      verbose_name="Дата последнего изменения")


    def __str__(self):
        return self.email


    class Meta:
        verbose_name = "получатель рассылки"
        verbose_name_plural = "получатели рассылки"
        ordering = ["owner", "email",]

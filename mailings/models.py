from django.db import models
from django.db.models import SET_NULL

from users.models import CustomUser


class Mailing(models.Model):
    """Модель сообщения"""
    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Текст письма")
    is_html = models.BooleanField(default=False, verbose_name="HTML формат")
    owner = models.ForeignKey(CustomUser,
                              on_delete=SET_NULL,
                              null=True,
                              blank=True,
                              related_name="mailings",
                              verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True,
                                      verbose_name="Дата последнего изменения")


    def __str__(self):
        return self.subject


    class Meta:
        verbose_name = "Cообщение"
        verbose_name_plural = "Cообщения"
        ordering = ["-created_at",]

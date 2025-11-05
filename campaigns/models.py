from django.db import models
from clients.models import Client
from mailings.models import Mailing
from users.models import CustomUser


class Campaign(models.Model):
    """Модель рассылки и управления статусами"""
    STATUS_CHOICES = [
        ("CREATED", "Создана"),
        ("RUNNING", "Запущена"),
        ("FINISHED", "Завершена"),
    ]

    name = models.CharField(max_length=255, verbose_name="Название рассылки")
    message = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="campaigns", verbose_name="Сообщение")
    recipients = models.ManyToManyField(Client, related_name="campaigns", verbose_name="Получатели рассылки")
    start_at = models.DateTimeField(verbose_name="Дата и время начала")
    end_at = models.DateTimeField(verbose_name="Дата и время окончания")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="CREATED", verbose_name="Статус")
    owner = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class Attempt(models.Model):
    """Модель попытки отправки рассылки"""
    STATUS_CHOICES = [
        ("SUCCESS", "Успешно"),
        ("FAIL", "Не успешно"),
    ]

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="attempts", verbose_name="Рассылка")
    recipient = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Получатель")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="Статус")
    response = models.TextField(blank=True, verbose_name="Ответ почтового сервера")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")

    def __str__(self):
        return f"{self.campaign.name} -> {self.recipient.email} ({self.get_status_display()})"

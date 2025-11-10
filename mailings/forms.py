from django import forms

from common.validate_utils import SpamChecker

from .models import Mailing


class MailingForm(forms.ModelForm):
    """Класс формы для создания сообщения"""

    class Meta:
        model = Mailing
        fields = ["subject", "body", "is_html"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 20}),
            "is_html": forms.Select(choices=[(True, "Да"), (False, "Нет")], attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        """Инициализация атрибутов класса"""
        super().__init__(*args, **kwargs)
        self.checker = SpamChecker()

    def clean_text_field(self, field_name):
        """Валидатор текстовых полей формы"""
        value = self.cleaned_data.get(field_name)
        self.checker.check_text(value)
        return value

    def clean_subject(self):
        """Метод валидации заголовка сообщения на спам и запрещенные слова"""
        return self.clean_text_field("subject")

    def clean_body(self):
        """Метод валидации текста сообщения на спам и запрещенные слова"""
        return self.clean_text_field("body")

from django import forms

from common.permissions import is_manager

from .models import Campaign


class CampaignForm(forms.ModelForm):
    """Форма для создания и редактирования рассылки"""

    class Meta:
        model = Campaign
        fields = ["name", "message", "recipients", "start_at", "end_at"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Select(attrs={"class": "form-select"}),
            "recipients": forms.SelectMultiple(attrs={"class": "form-select", "multiple": True}),
            "start_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        """Ограничивает выпадающий список сообщений и клиентов только теми, что созданы пользователем"""
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user and not is_manager(user):
            self.fields["message"].queryset = self.fields["message"].queryset.filter(owner=user)
            self.fields["recipients"].queryset = self.fields["recipients"].queryset.filter(owner=user)

    def clean(self):
        """Проверяет, что дата окончания позже даты начала"""
        cleaned_data = super().clean()
        start_at = cleaned_data.get("start_at")
        end_at = cleaned_data.get("end_at")

        if start_at and end_at and start_at >= end_at:
            raise forms.ValidationError("Дата окончания рассылки должна быть позже даты начала")

        return cleaned_data

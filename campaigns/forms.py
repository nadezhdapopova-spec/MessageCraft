from django import forms
from .models import Campaign


class CampaignForm(forms.ModelForm):
    """Форма для создания и редактирования рассылки"""

    class Meta:
        model = Campaign
        fields = ["name", "message", "recipients", "start_at", "end_at"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Select(attrs={"class": "form-select"}),
            "recipients": forms.SelectMultiple(attrs={"class": "form-select"}),
            "start_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        }

    def clean(self):
        """Проверяет, что дата окончания позже даты начала"""
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("Дата окончания рассылки должна быть позже даты начала")

        return cleaned_data

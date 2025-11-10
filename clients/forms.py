from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    """Форма для создания получателя рассылки"""

    class Meta:
        model = Client
        fields = ["email", "full_name", "comment"]
        widgets = {
            "email": forms.TextInput(attrs={"class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "comment": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Не более 500 символов"}
            ),
        }

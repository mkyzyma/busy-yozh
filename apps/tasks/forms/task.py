from django import forms

from apps.accounts.models import User
from apps.tasks.models import Task


class TaskForm(forms.ModelForm):
    assignee = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("username"),
        required=False,
        empty_label="Не назначен",
        label="Исполнитель",
    )

    class Meta:
        model = Task
        fields = ("title", "description", "assignee")
        labels = {
            "title": "Название",
            "description": "Описание",
        }

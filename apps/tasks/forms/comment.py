from django import forms

from apps.tasks.models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {"text": "Новый комментарий"}
        widgets = {
            "text": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Добавьте детали или вопрос"}
            )
        }

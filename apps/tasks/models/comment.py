from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models

from apps.tasks.models.task import Task


class Comment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField(validators=[MaxLengthValidator(5000)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def clean(self) -> None:
        self.text = self.text.strip()
        if not self.text:
            raise ValidationError({"text": "Comment cannot be blank."})

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.task}"

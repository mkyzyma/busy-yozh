from django.db.models import QuerySet

from apps.tasks.models import Comment, Task


def get_task_comments(*, task: Task) -> QuerySet[Comment]:
    return Comment.objects.filter(task=task).select_related("author")

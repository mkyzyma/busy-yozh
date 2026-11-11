from django.db.models import QuerySet

from apps.tasks.models import Task


def get_tasks(
    *,
    author_id: int | None = None,
    assignee_id: int | None = None,
    is_completed: bool | None = None,
) -> QuerySet[Task]:
    tasks = Task.objects.select_related("author", "assignee")
    if author_id is not None:
        tasks = tasks.filter(author_id=author_id)
    if assignee_id is not None:
        tasks = tasks.filter(assignee_id=assignee_id)
    if is_completed is not None:
        tasks = tasks.filter(is_completed=is_completed)
    return tasks

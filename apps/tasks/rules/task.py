from apps.accounts.models import User
from apps.tasks.models import Task


def can_edit_task(*, user: User, task: Task) -> bool:
    return user.is_authenticated and user.pk == task.author_id


def can_change_task_completion(*, user: User, task: Task) -> bool:
    return user.is_authenticated and user.pk in {task.author_id, task.assignee_id}

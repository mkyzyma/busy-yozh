from django.core.exceptions import PermissionDenied

from apps.accounts.models import User
from apps.tasks.models import Task
from apps.tasks.rules import can_change_task_completion, can_edit_task


def create_task(
    *,
    author: User,
    title: str,
    description: str = "",
    assignee: User | None = None,
) -> Task:
    task = Task(
        author=author,
        title=title,
        description=description,
        assignee=assignee,
    )
    task.full_clean()
    task.save()
    return task


def update_task(
    *,
    task: Task,
    actor: User,
    title: str,
    description: str = "",
    assignee: User | None = None,
) -> Task:
    if not can_edit_task(user=actor, task=task):
        raise PermissionDenied

    task.title = title
    task.description = description
    task.assignee = assignee
    task.full_clean()
    task.save()
    return task


def delete_task(*, task: Task, actor: User) -> None:
    if not can_edit_task(user=actor, task=task):
        raise PermissionDenied
    task.delete()


def set_task_completion(
    *,
    task: Task,
    actor: User,
    is_completed: bool,
) -> Task:
    if not can_change_task_completion(user=actor, task=task):
        raise PermissionDenied
    if task.is_completed == is_completed:
        return task

    task.is_completed = is_completed
    task.save(update_fields=["is_completed", "updated_at"])
    return task

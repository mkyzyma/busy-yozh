from django.core.exceptions import PermissionDenied

from apps.accounts.models import User
from apps.tasks.models import Comment, Task
from apps.tasks.rules import can_comment_task


def add_comment(*, task: Task, author: User, text: str) -> Comment:
    if not can_comment_task(user=author, task=task):
        raise PermissionDenied

    comment = Comment(task=task, author=author, text=text)
    comment.full_clean()
    comment.save()
    return comment

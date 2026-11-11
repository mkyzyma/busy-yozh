from apps.accounts.models import User
from apps.tasks.models import Task


def can_comment_task(*, user: User, task: Task) -> bool:
    return user.is_authenticated

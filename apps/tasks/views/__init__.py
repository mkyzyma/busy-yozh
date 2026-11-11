from apps.tasks.views.comment import comment_create
from apps.tasks.views.completion import task_completion
from apps.tasks.views.task import (
    TaskCreateView,
    TaskDeleteView,
    TaskDetailView,
    TaskListView,
    TaskUpdateView,
)

__all__ = [
    "TaskCreateView",
    "TaskDeleteView",
    "TaskDetailView",
    "TaskListView",
    "TaskUpdateView",
    "comment_create",
    "task_completion",
]

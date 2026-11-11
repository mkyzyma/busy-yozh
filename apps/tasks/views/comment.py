from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.tasks.forms import CommentForm
from apps.tasks.rules import can_change_task_completion, can_comment_task, can_edit_task
from apps.tasks.selectors import get_task_comments, get_tasks
from apps.tasks.services import add_comment


@login_required
@require_POST
def comment_create(request: HttpRequest, task_id: int) -> HttpResponse:
    task = get_object_or_404(get_tasks(), pk=task_id)
    actor = cast(User, request.user)
    if not can_comment_task(user=actor, task=task):
        raise PermissionDenied

    form = CommentForm(request.POST)
    if form.is_valid():
        add_comment(task=task, author=actor, text=form.cleaned_data["text"])
        messages.success(request, "Комментарий добавлен.")
        return redirect("tasks:task-detail", pk=task.pk)

    return render(
        request,
        "tasks/task_detail.html",
        {
            "task": task,
            "comments": get_task_comments(task=task),
            "comment_form": form,
            "can_edit": can_edit_task(user=actor, task=task),
            "can_change_completion": can_change_task_completion(
                user=actor,
                task=task,
            ),
        },
        status=400,
    )

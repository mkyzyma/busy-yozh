from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.accounts.models import User
from apps.tasks.rules import can_change_task_completion
from apps.tasks.selectors import get_tasks
from apps.tasks.services import set_task_completion


@login_required
@require_POST
def task_completion(request: HttpRequest, task_id: int) -> HttpResponse:
    task = get_object_or_404(get_tasks(), pk=task_id)
    actor = cast(User, request.user)
    if not can_change_task_completion(user=actor, task=task):
        raise PermissionDenied

    desired_state = request.POST.get("is_completed")
    if desired_state not in {"true", "false"}:
        return HttpResponseBadRequest("Expected is_completed=true or false.")

    set_task_completion(
        task=task,
        actor=actor,
        is_completed=desired_state == "true",
    )
    messages.success(request, "Статус задачи обновлён.")
    return redirect("tasks:task-detail", pk=task.pk)

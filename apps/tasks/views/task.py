from typing import TYPE_CHECKING, Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, FormView, ListView, UpdateView

from apps.accounts.models import User
from apps.tasks.forms import CommentForm, TaskForm
from apps.tasks.models import Task
from apps.tasks.rules import can_change_task_completion, can_edit_task
from apps.tasks.selectors import get_task_comments, get_tasks
from apps.tasks.services import create_task, delete_task, update_task


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Task]:
        scope = self.request.GET.get("scope", "all")
        status = self.request.GET.get("status", "all")
        author_id = None
        assignee_id = None
        is_completed = None

        if scope == "mine":
            author_id = cast(int, self.request.user.pk)
        elif scope == "assigned":
            assignee_id = cast(int, self.request.user.pk)

        if status == "active":
            is_completed = False
        elif status == "completed":
            is_completed = True

        return get_tasks(
            author_id=author_id,
            assignee_id=assignee_id,
            is_completed=is_completed,
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        scope = self.request.GET.get("scope", "all")
        status = self.request.GET.get("status", "all")
        context["scope"] = scope if scope in {"all", "mine", "assigned"} else "all"
        context["status"] = (
            status if status in {"all", "active", "completed"} else "all"
        )
        return context


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_queryset(self) -> QuerySet[Task]:
        return get_tasks()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        task = cast(Task, self.object)
        actor = cast(User, self.request.user)
        context["comments"] = get_task_comments(task=task)
        context["comment_form"] = CommentForm()
        context["can_edit"] = can_edit_task(user=actor, task=task)
        context["can_change_completion"] = can_change_task_completion(
            user=actor,
            task=task,
        )
        return context


class TaskCreateView(LoginRequiredMixin, FormView):
    template_name = "tasks/task_form.html"
    form_class = TaskForm

    def form_valid(self, form):
        task = create_task(
            author=cast(User, self.request.user),
            **form.cleaned_data,
        )
        messages.success(self.request, "Задача создана.")
        return redirect("tasks:task-detail", pk=task.pk)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Новая задача"
        context["submit_label"] = "Создать задачу"
        return context


class TaskAuthorRequiredMixin(UserPassesTestMixin):
    if TYPE_CHECKING:
        request: Any

        def get_object(self, queryset: Any = None) -> Task: ...

    def test_func(self) -> bool:
        return can_edit_task(user=self.request.user, task=self.get_object())

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class TaskUpdateView(LoginRequiredMixin, TaskAuthorRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"
    context_object_name = "task"

    def get_queryset(self) -> QuerySet[Task]:
        return get_tasks()

    def form_valid(self, form):
        self.object = update_task(
            task=cast(Task, self.object),
            actor=cast(User, self.request.user),
            **form.cleaned_data,
        )
        messages.success(self.request, "Изменения сохранены.")
        return redirect("tasks:task-detail", pk=self.object.pk)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Редактирование задачи"
        context["submit_label"] = "Сохранить изменения"
        return context


class TaskDeleteView(LoginRequiredMixin, TaskAuthorRequiredMixin, DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"
    context_object_name = "task"
    success_url = reverse_lazy("tasks:task-list")

    def get_queryset(self) -> QuerySet[Task]:
        return get_tasks()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        delete_task(
            task=cast(Task, self.object),
            actor=cast(User, self.request.user),
        )
        messages.success(request, "Задача удалена.")
        return redirect(self.success_url)

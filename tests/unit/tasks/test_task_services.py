import pytest
from django.core.exceptions import PermissionDenied

from apps.tasks.models import Task
from apps.tasks.services import (
    create_task,
    delete_task,
    set_task_completion,
    update_task,
)
from tests.factories.tasks import TaskFactory

pytestmark = pytest.mark.django_db


def test_only_author_can_update_and_delete(author, other):
    task = create_task(author=author, title="Original")

    with pytest.raises(PermissionDenied):
        update_task(task=task, actor=other, title="Changed")
    task.refresh_from_db()
    assert task.title == "Original"

    updated = update_task(task=task, actor=author, title="Changed")
    assert updated.title == "Changed"

    with pytest.raises(PermissionDenied):
        delete_task(task=task, actor=other)
    assert Task.objects.filter(pk=task.pk).exists()

    delete_task(task=task, actor=author)
    assert not Task.objects.filter(pk=task.pk).exists()


def test_author_or_assignee_can_complete(author, assignee, other):
    task = TaskFactory(author=author, assignee=assignee)

    set_task_completion(task=task, actor=assignee, is_completed=True)
    assert task.is_completed is True

    set_task_completion(task=task, actor=author, is_completed=False)
    assert task.is_completed is False

    with pytest.raises(PermissionDenied):
        set_task_completion(task=task, actor=other, is_completed=True)
    task.refresh_from_db()
    assert task.is_completed is False


def test_set_completion_is_idempotent(author, django_assert_num_queries):
    task = TaskFactory(author=author)

    set_task_completion(task=task, actor=author, is_completed=True)
    updated_at = task.updated_at
    with django_assert_num_queries(0):
        repeated = set_task_completion(task=task, actor=author, is_completed=True)

    assert repeated.is_completed is True
    assert repeated.updated_at == updated_at


def test_update_can_assign_and_unassign(author, assignee):
    task = TaskFactory(author=author, assignee=None)

    update_task(task=task, actor=author, title=task.title, assignee=assignee)
    assert task.assignee == assignee

    update_task(task=task, actor=author, title=task.title, assignee=None)
    assert task.assignee is None

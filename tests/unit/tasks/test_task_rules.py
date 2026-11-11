import pytest
from django.contrib.auth.models import AnonymousUser

from apps.tasks.rules import can_change_task_completion, can_edit_task
from tests.factories.tasks import TaskFactory

pytestmark = pytest.mark.django_db


def test_only_author_can_edit(author, other):
    task = TaskFactory(author=author)

    assert can_edit_task(user=author, task=task) is True
    assert can_edit_task(user=other, task=task) is False
    assert can_edit_task(user=AnonymousUser(), task=task) is False


def test_author_or_assignee_can_change_completion(author, assignee, other):
    task = TaskFactory(author=author, assignee=assignee)

    assert can_change_task_completion(user=author, task=task) is True
    assert can_change_task_completion(user=assignee, task=task) is True
    assert can_change_task_completion(user=other, task=task) is False
    assert can_change_task_completion(user=AnonymousUser(), task=task) is False


def test_unassigned_task_only_allows_author_to_change_completion(author, other):
    task = TaskFactory(author=author, assignee=None)

    assert can_change_task_completion(user=author, task=task) is True
    assert can_change_task_completion(user=other, task=task) is False

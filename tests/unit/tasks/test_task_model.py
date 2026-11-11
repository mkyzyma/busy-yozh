import pytest
from django.core.exceptions import ValidationError

from apps.tasks.models import Task
from apps.tasks.services import create_task

pytestmark = pytest.mark.django_db


def test_task_defaults_to_incomplete(author):
    task = create_task(author=author, title="Write documentation")

    assert task.is_completed is False
    assert task.author == author


def test_task_service_rejects_whitespace_title(author):
    with pytest.raises(ValidationError):
        create_task(author=author, title="   ")

    assert Task.objects.count() == 0


def test_task_title_longer_than_200_is_rejected(author):
    with pytest.raises(ValidationError):
        create_task(author=author, title="x" * 201)

    assert Task.objects.count() == 0


def test_deleting_assignee_keeps_task(author, assignee):
    task = create_task(author=author, title="Review", assignee=assignee)

    assignee.delete()
    task.refresh_from_db()

    assert Task.objects.filter(pk=task.pk).exists()
    assert task.assignee_id is None

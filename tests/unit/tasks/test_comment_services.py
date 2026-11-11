import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from apps.tasks.rules import can_comment_task
from apps.tasks.services import add_comment
from tests.factories.tasks import TaskFactory

pytestmark = pytest.mark.django_db


def test_add_comment_sets_author_and_task(author):
    task = TaskFactory(author=author)

    comment = add_comment(task=task, author=author, text="  Looks good  ")

    assert comment.task == task
    assert comment.author == author
    assert comment.text == "Looks good"


def test_any_authenticated_user_can_comment(author, other):
    task = TaskFactory(author=author)

    comment = add_comment(task=task, author=other, text="I can help")

    assert comment.author == other
    assert can_comment_task(user=other, task=task) is True


def test_anonymous_user_cannot_comment(author):
    task = TaskFactory(author=author)
    anonymous = AnonymousUser()

    assert can_comment_task(user=anonymous, task=task) is False
    with pytest.raises(PermissionDenied):
        add_comment(task=task, author=anonymous, text="Anonymous")

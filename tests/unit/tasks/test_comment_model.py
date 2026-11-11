import pytest
from django.core.exceptions import ValidationError

from apps.tasks.models import Comment
from apps.tasks.services import add_comment
from tests.factories.tasks import TaskFactory

pytestmark = pytest.mark.django_db


def test_comment_service_rejects_whitespace_text(author):
    task = TaskFactory(author=author)

    with pytest.raises(ValidationError):
        add_comment(task=task, author=author, text="   ")

    assert Comment.objects.count() == 0


def test_comment_text_longer_than_5000_is_rejected(author):
    task = TaskFactory(author=author)

    with pytest.raises(ValidationError):
        add_comment(task=task, author=author, text="x" * 5001)

    assert Comment.objects.count() == 0

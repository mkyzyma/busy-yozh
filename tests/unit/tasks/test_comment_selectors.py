import pytest

from apps.tasks.selectors import get_task_comments
from tests.factories import UserFactory
from tests.factories.tasks import CommentFactory, TaskFactory

pytestmark = pytest.mark.django_db


def test_comments_are_chronological(author):
    task = TaskFactory(author=author)
    first = CommentFactory(task=task, author=author, text="First")
    second = CommentFactory(task=task, author=author, text="Second")
    third = CommentFactory(task=task, author=author, text="Third")

    assert list(get_task_comments(task=task)) == [first, second, third]


def test_comment_selector_prefetches_author(author, django_assert_num_queries):
    task = TaskFactory(author=author)
    other = UserFactory()
    CommentFactory(task=task, author=author)
    CommentFactory(task=task, author=other)

    with django_assert_num_queries(1):
        comments = list(get_task_comments(task=task))
        assert [comment.author.username for comment in comments] == [
            author.username,
            other.username,
        ]

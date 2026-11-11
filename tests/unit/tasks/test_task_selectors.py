import pytest

from apps.tasks.selectors import get_tasks
from tests.factories import UserFactory
from tests.factories.tasks import TaskFactory

pytestmark = pytest.mark.django_db


def test_get_tasks_filters_by_author_assignee_and_status(author, assignee):
    other_author = UserFactory()
    matching = TaskFactory(
        author=author,
        assignee=assignee,
        is_completed=True,
    )
    other_completed = TaskFactory(
        author=other_author,
        assignee=assignee,
        is_completed=True,
    )
    uncompleted = TaskFactory(author=author, assignee=None, is_completed=False)

    assert set(get_tasks(author_id=author.id).values_list("id", flat=True)) == {
        matching.id,
        uncompleted.id,
    }
    assert set(
        get_tasks(assignee_id=assignee.id, is_completed=True).values_list(
            "id", flat=True
        )
    ) == {matching.id, other_completed.id}
    assert list(get_tasks(is_completed=False)).count(matching) == 0
    assert list(
        get_tasks(
            author_id=author.id,
            assignee_id=assignee.id,
            is_completed=True,
        )
    ) == [matching]


def test_get_tasks_uses_related_users(author, assignee, django_assert_num_queries):
    TaskFactory(author=author, assignee=assignee)
    TaskFactory(author=author, assignee=None)

    with django_assert_num_queries(1):
        tasks = list(get_tasks())
        for task in tasks:
            assert task.author.username
            if task.assignee:
                assert task.assignee.username

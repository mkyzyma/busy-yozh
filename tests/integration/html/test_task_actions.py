import pytest
from django.test import Client
from django.urls import reverse

from apps.tasks.models import Comment
from tests.factories import UserFactory
from tests.factories.tasks import CommentFactory, TaskFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def author():
    return UserFactory()


@pytest.fixture
def assignee():
    return UserFactory()


@pytest.fixture
def other():
    return UserFactory()


def test_author_and_assignee_can_complete_and_reopen(client, author, assignee):
    task = TaskFactory(author=author, assignee=assignee, is_completed=False)
    url = reverse("tasks:task-completion", args=[task.id])

    client.force_login(assignee)
    complete_response = client.post(url, {"is_completed": "true"})
    task.refresh_from_db()
    assert complete_response.status_code == 302
    assert complete_response.url == reverse("tasks:task-detail", args=[task.id])
    assert task.is_completed is True

    client.force_login(author)
    reopen_response = client.post(url, {"is_completed": "false"})
    task.refresh_from_db()
    assert reopen_response.status_code == 302
    assert task.is_completed is False


def test_other_user_cannot_change_completion(client, other):
    task = TaskFactory(is_completed=False)
    client.force_login(other)

    response = client.post(
        reverse("tasks:task-completion", args=[task.id]),
        {"is_completed": "true"},
    )

    assert response.status_code == 403
    task.refresh_from_db()
    assert task.is_completed is False


def test_completion_get_is_not_allowed(client, author):
    task = TaskFactory(author=author, is_completed=False)
    client.force_login(author)

    response = client.get(reverse("tasks:task-completion", args=[task.id]))

    assert response.status_code == 405
    task.refresh_from_db()
    assert task.is_completed is False


@pytest.mark.parametrize("payload", [{}, {"is_completed": "maybe"}])
def test_completion_requires_valid_boolean(client, author, payload):
    task = TaskFactory(author=author, is_completed=False)
    client.force_login(author)

    response = client.post(reverse("tasks:task-completion", args=[task.id]), payload)

    assert response.status_code == 400
    task.refresh_from_db()
    assert task.is_completed is False


def test_user_can_add_comment(client, author, other):
    task = TaskFactory(author=author)
    client.force_login(other)

    response = client.post(
        reverse("tasks:comment-create", args=[task.id]),
        {"text": "I can help with this"},
    )

    assert response.status_code == 302
    assert response.url == reverse("tasks:task-detail", args=[task.id])
    comment = Comment.objects.get()
    assert comment.author == other
    assert comment.task == task
    assert comment.text == "I can help with this"


def test_blank_comment_rerenders_detail_with_errors(client, author):
    task = TaskFactory(author=author)
    client.force_login(author)

    response = client.post(
        reverse("tasks:comment-create", args=[task.id]),
        {"text": "   "},
    )

    assert response.status_code == 400
    assert "text" in response.context["comment_form"].errors
    assert response.context["task"] == task
    assert Comment.objects.count() == 0


def test_comment_get_is_not_allowed(client, author):
    task = TaskFactory(author=author)
    client.force_login(author)

    response = client.get(reverse("tasks:comment-create", args=[task.id]))

    assert response.status_code == 405
    assert Comment.objects.count() == 0


def test_comment_list_is_visible_on_detail(client, author):
    task = TaskFactory(author=author)
    CommentFactory(task=task, author=author, text="First comment")
    CommentFactory(task=task, author=author, text="Second comment")
    client.force_login(author)

    response = client.get(reverse("tasks:task-detail", args=[task.id]))
    content = response.content.decode()

    assert response.status_code == 200
    assert content.index("First comment") < content.index("Second comment")


def test_mutating_html_forms_require_csrf(author):
    task = TaskFactory(author=author, is_completed=False)
    client = Client(enforce_csrf_checks=True)
    client.force_login(author)

    response = client.post(
        reverse("tasks:task-completion", args=[task.id]),
        {"is_completed": "true"},
    )

    assert response.status_code == 403
    task.refresh_from_db()
    assert task.is_completed is False

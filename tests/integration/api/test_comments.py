import pytest

from apps.tasks.models import Comment
from tests.factories import UserFactory
from tests.factories.tasks import CommentFactory, TaskFactory

pytestmark = pytest.mark.django_db


def test_create_comment_uses_token_user(authenticated_api_client):
    task = TaskFactory()
    client = authenticated_api_client(task.author)

    response = client.post(
        f"/api/v1/tasks/{task.id}/comments/",
        {"text": "Looks good"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["author"] == task.author_id
    assert response.data["task"] == task.id
    assert response.data["text"] == "Looks good"


@pytest.mark.parametrize("text", ["", "   "])
def test_create_comment_rejects_blank_text(authenticated_api_client, text):
    task = TaskFactory()
    client = authenticated_api_client(task.author)

    response = client.post(
        f"/api/v1/tasks/{task.id}/comments/", {"text": text}, format="json"
    )

    assert response.status_code == 400
    assert Comment.objects.count() == 0


def test_create_comment_rejects_text_over_5000(authenticated_api_client):
    task = TaskFactory()
    client = authenticated_api_client(task.author)

    response = client.post(
        f"/api/v1/tasks/{task.id}/comments/", {"text": "x" * 5001}, format="json"
    )

    assert response.status_code == 400
    assert Comment.objects.count() == 0


def test_comment_list_is_chronological_and_paginated(authenticated_api_client):
    task = TaskFactory()
    comments = CommentFactory.create_batch(21, task=task)
    client = authenticated_api_client(task.author)

    response = client.get(f"/api/v1/tasks/{task.id}/comments/")

    assert response.status_code == 200
    assert response.data["count"] == 21
    assert len(response.data["results"]) == 20
    assert response.data["results"][0]["id"] == comments[0].id
    assert response.data["next"] is not None

    second_page = client.get(response.data["next"])
    assert second_page.status_code == 200
    assert len(second_page.data["results"]) == 1


def test_comment_author_and_task_are_read_only(authenticated_api_client):
    task = TaskFactory()
    other_task = TaskFactory()
    other = UserFactory()
    client = authenticated_api_client(task.author)

    response = client.post(
        f"/api/v1/tasks/{task.id}/comments/",
        {"text": "Server-owned fields", "task": other_task.id, "author": other.id},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["task"] == task.id
    assert response.data["author"] == task.author_id


def test_any_authenticated_user_can_comment(authenticated_api_client):
    task = TaskFactory()
    other = UserFactory()
    client = authenticated_api_client(other)

    response = client.post(
        f"/api/v1/tasks/{task.id}/comments/",
        {"text": "I can help"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["author"] == other.id


def test_anonymous_comment_requests_return_401(api_client):
    task = TaskFactory()

    response = api_client.get(f"/api/v1/tasks/{task.id}/comments/")

    assert response.status_code == 401


def test_comments_for_missing_task_return_404(authenticated_api_client):
    client = authenticated_api_client(UserFactory())

    response = client.get("/api/v1/tasks/999999/comments/")

    assert response.status_code == 404

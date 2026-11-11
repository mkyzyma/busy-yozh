import pytest

from tests.factories import UserFactory
from tests.factories.tasks import TaskFactory

pytestmark = pytest.mark.django_db


def test_author_and_assignee_can_set_completion(authenticated_api_client):
    author = UserFactory()
    assignee = UserFactory()
    task = TaskFactory(author=author, assignee=assignee, is_completed=False)

    assignee_response = authenticated_api_client(assignee).post(
        f"/api/v1/tasks/{task.id}/completion/",
        {"is_completed": True},
        format="json",
    )
    assert assignee_response.status_code == 200
    assert assignee_response.data["is_completed"] is True

    author_response = authenticated_api_client(author).post(
        f"/api/v1/tasks/{task.id}/completion/",
        {"is_completed": False},
        format="json",
    )
    assert author_response.status_code == 200
    assert author_response.data["is_completed"] is False


def test_other_user_cannot_change_completion(authenticated_api_client):
    task = TaskFactory(is_completed=False)
    client = authenticated_api_client(UserFactory())

    response = client.post(
        f"/api/v1/tasks/{task.id}/completion/",
        {"is_completed": True},
        format="json",
    )

    assert response.status_code == 403
    task.refresh_from_db()
    assert task.is_completed is False


@pytest.mark.parametrize("payload", [{}, {"is_completed": "not-a-boolean"}])
def test_completion_requires_explicit_boolean(authenticated_api_client, payload):
    task = TaskFactory()
    client = authenticated_api_client(task.author)

    response = client.post(
        f"/api/v1/tasks/{task.id}/completion/", payload, format="json"
    )

    assert response.status_code == 400


def test_completion_repeat_returns_current_state(authenticated_api_client):
    task = TaskFactory(is_completed=False)
    client = authenticated_api_client(task.author)
    url = f"/api/v1/tasks/{task.id}/completion/"

    first = client.post(url, {"is_completed": True}, format="json")
    second = client.post(url, {"is_completed": True}, format="json")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.data["is_completed"] is True
    assert second.data["is_completed"] is True


def test_completion_does_not_allow_task_field_changes(authenticated_api_client):
    author = UserFactory()
    other = UserFactory()
    task = TaskFactory(author=author, title="Original", is_completed=False)
    client = authenticated_api_client(author)

    response = client.post(
        f"/api/v1/tasks/{task.id}/completion/",
        {"is_completed": True, "title": "Changed", "author": other.id},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["is_completed"] is True
    task.refresh_from_db()
    assert task.title == "Original"
    assert task.author == author


def test_anonymous_completion_returns_401(api_client):
    task = TaskFactory()

    response = api_client.post(
        f"/api/v1/tasks/{task.id}/completion/",
        {"is_completed": True},
        format="json",
    )

    assert response.status_code == 401


def test_completion_for_missing_task_returns_404(authenticated_api_client):
    client = authenticated_api_client(UserFactory())

    response = client.post(
        "/api/v1/tasks/999999/completion/",
        {"is_completed": True},
        format="json",
    )

    assert response.status_code == 404

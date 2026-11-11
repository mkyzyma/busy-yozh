import pytest

from apps.tasks.models import Task
from tests.factories import UserFactory
from tests.factories.tasks import TaskFactory

pytestmark = pytest.mark.django_db


def test_create_task_uses_token_user_as_author(authenticated_api_client):
    author = UserFactory()
    assignee = UserFactory()
    client = authenticated_api_client(author)

    response = client.post(
        "/api/v1/tasks/",
        {
            "title": "Prepare release",
            "description": "Check all deployment steps",
            "assignee": assignee.id,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["author"] == author.id
    assert response.data["assignee"] == assignee.id
    assert response.data["is_completed"] is False
    task = Task.objects.get(pk=response.data["id"])
    assert task.author == author
    assert task.assignee == assignee


@pytest.mark.parametrize("title", ["", "   "])
def test_create_task_rejects_blank_title(authenticated_api_client, title):
    client = authenticated_api_client(UserFactory())

    response = client.post("/api/v1/tasks/", {"title": title}, format="json")

    assert response.status_code == 400
    assert Task.objects.count() == 0


def test_create_task_rejects_title_over_200(authenticated_api_client):
    client = authenticated_api_client(UserFactory())

    response = client.post("/api/v1/tasks/", {"title": "x" * 201}, format="json")

    assert response.status_code == 400
    assert Task.objects.count() == 0


def test_assign_nonexistent_user_returns_400(authenticated_api_client):
    client = authenticated_api_client(UserFactory())

    response = client.post(
        "/api/v1/tasks/",
        {"title": "Invalid assignee", "assignee": 999999},
        format="json",
    )

    assert response.status_code == 400
    assert Task.objects.count() == 0


def test_author_cannot_be_changed_through_payload(authenticated_api_client):
    author = UserFactory()
    other = UserFactory()
    task = TaskFactory(author=author, title="Original")
    client = authenticated_api_client(author)

    response = client.patch(
        f"/api/v1/tasks/{task.id}/",
        {"title": "Updated", "author": other.id},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["author"] == author.id
    task.refresh_from_db()
    assert task.author == author
    assert task.title == "Updated"


def test_completion_is_read_only_in_general_task_endpoint(authenticated_api_client):
    author = UserFactory()
    task = TaskFactory(author=author, is_completed=False)
    client = authenticated_api_client(author)

    response = client.patch(
        f"/api/v1/tasks/{task.id}/",
        {"is_completed": True},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["is_completed"] is False
    task.refresh_from_db()
    assert task.is_completed is False


def test_task_list_filters_and_paginates(authenticated_api_client):
    author = UserFactory()
    assignee = UserFactory()
    tasks = TaskFactory.create_batch(
        21,
        author=author,
        assignee=assignee,
        is_completed=True,
    )
    TaskFactory(is_completed=False)
    client = authenticated_api_client(author)

    response = client.get(
        "/api/v1/tasks/",
        {"author": author.id, "assignee": assignee.id, "is_completed": "true"},
    )

    assert response.status_code == 200
    assert response.data["count"] == 21
    assert len(response.data["results"]) == 20
    assert response.data["next"] is not None
    assert response.data["previous"] is None
    expected_ids = {task.id for task in tasks}
    assert {item["id"] for item in response.data["results"]} <= expected_ids

    second_page = client.get(response.data["next"])
    assert second_page.status_code == 200
    assert len(second_page.data["results"]) == 1
    assert second_page.data["previous"] is not None


@pytest.mark.parametrize(
    "query",
    ["author=not-an-int", "assignee=0", "is_completed=not-a-boolean"],
)
def test_invalid_task_filters_return_400(authenticated_api_client, query):
    client = authenticated_api_client(UserFactory())

    response = client.get(f"/api/v1/tasks/?{query}")

    assert response.status_code == 400


def test_other_user_cannot_update_or_delete_task(authenticated_api_client):
    author = UserFactory()
    other = UserFactory()
    task = TaskFactory(author=author, title="Protected", description="Original")
    client = authenticated_api_client(other)

    patch_response = client.patch(
        f"/api/v1/tasks/{task.id}/", {"title": "Changed"}, format="json"
    )
    put_response = client.put(
        f"/api/v1/tasks/{task.id}/",
        {"title": "Changed", "description": "Changed", "assignee": None},
        format="json",
    )
    delete_response = client.delete(f"/api/v1/tasks/{task.id}/")

    assert patch_response.status_code == 403
    assert put_response.status_code == 403
    assert delete_response.status_code == 403
    task.refresh_from_db()
    assert task.title == "Protected"
    assert task.description == "Original"
    assert Task.objects.filter(pk=task.pk).exists()


def test_author_can_update_assignee_and_delete_task(authenticated_api_client):
    author = UserFactory()
    assignee = UserFactory()
    task = TaskFactory(author=author, assignee=None)
    client = authenticated_api_client(author)

    response = client.patch(
        f"/api/v1/tasks/{task.id}/", {"assignee": assignee.id}, format="json"
    )

    assert response.status_code == 200
    assert response.data["assignee"] == assignee.id
    task.refresh_from_db()
    assert task.assignee == assignee

    delete_response = client.delete(f"/api/v1/tasks/{task.id}/")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/tasks/{task.id}/").status_code == 404


def test_unfiltered_task_list_includes_active_and_completed(authenticated_api_client):
    active = TaskFactory(is_completed=False)
    completed = TaskFactory(is_completed=True)
    client = authenticated_api_client(UserFactory())

    response = client.get("/api/v1/tasks/")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert {item["id"] for item in response.data["results"]} == {
        active.id,
        completed.id,
    }


def test_any_authenticated_user_can_view_task(authenticated_api_client):
    task = TaskFactory(is_completed=True)
    client = authenticated_api_client(UserFactory())

    response = client.get(f"/api/v1/tasks/{task.id}/")

    assert response.status_code == 200
    assert response.data["id"] == task.id


def test_anonymous_task_requests_return_401(api_client):
    response = api_client.get("/api/v1/tasks/")

    assert response.status_code == 401


def test_missing_task_returns_404(authenticated_api_client):
    client = authenticated_api_client(UserFactory())

    response = client.get("/api/v1/tasks/999999/")

    assert response.status_code == 404

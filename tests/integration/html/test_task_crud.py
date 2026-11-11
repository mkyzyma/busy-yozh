import pytest
from django.urls import reverse

from apps.tasks.models import Task
from tests.factories import UserFactory
from tests.factories.tasks import TaskFactory

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


def task_ids(response):
    return {task.id for task in response.context["tasks"]}


def test_task_pages_require_login(client):
    task = TaskFactory()
    urls = [
        reverse("tasks:task-list"),
        reverse("tasks:task-create"),
        reverse("tasks:task-detail", args=[task.id]),
        reverse("tasks:task-update", args=[task.id]),
        reverse("tasks:task-delete", args=[task.id]),
    ]

    for url in urls:
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith("/accounts/login/?next=")


def test_create_task(client, author, assignee):
    client.force_login(author)

    response = client.post(
        reverse("tasks:task-create"),
        {
            "title": "Prepare demo",
            "description": "Show the complete workflow",
            "assignee": assignee.id,
        },
    )

    task = Task.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("tasks:task-detail", args=[task.id])
    assert task.author == author
    assert task.assignee == assignee


def test_create_task_invalid_form_rerenders(client, author):
    client.force_login(author)

    response = client.post(
        reverse("tasks:task-create"),
        {"title": "   ", "description": "Invalid", "assignee": ""},
    )

    assert response.status_code == 200
    assert "title" in response.context["form"].errors
    assert Task.objects.count() == 0


def test_task_list_scope_and_status_filters(client, author, other):
    mine_active = TaskFactory(author=author, is_completed=False)
    mine_completed = TaskFactory(author=author, is_completed=True)
    assigned_active = TaskFactory(author=other, assignee=author, is_completed=False)
    other_task = TaskFactory(author=other, assignee=None, is_completed=False)
    client.force_login(author)

    default_response = client.get(reverse("tasks:task-list"))
    assert task_ids(default_response) == {
        mine_active.id,
        mine_completed.id,
        assigned_active.id,
        other_task.id,
    }

    mine_response = client.get(reverse("tasks:task-list"), {"scope": "mine"})
    assert task_ids(mine_response) == {mine_active.id, mine_completed.id}

    assigned_response = client.get(reverse("tasks:task-list"), {"scope": "assigned"})
    assert task_ids(assigned_response) == {assigned_active.id}

    active_response = client.get(reverse("tasks:task-list"), {"status": "active"})
    assert task_ids(active_response) == {
        mine_active.id,
        assigned_active.id,
        other_task.id,
    }

    completed_response = client.get(reverse("tasks:task-list"), {"status": "completed"})
    assert task_ids(completed_response) == {mine_completed.id}


def test_invalid_html_filters_show_default_list(client, author, other):
    first = TaskFactory(author=author)
    second = TaskFactory(author=other)
    client.force_login(author)

    response = client.get(
        reverse("tasks:task-list"),
        {"scope": "unknown", "status": "unknown"},
    )

    assert response.status_code == 200
    assert task_ids(response) == {first.id, second.id}
    assert response.context["scope"] == "all"
    assert response.context["status"] == "all"


def test_task_list_paginates_by_20(client, author):
    TaskFactory.create_batch(21, author=author)
    client.force_login(author)

    first_page = client.get(reverse("tasks:task-list"))
    second_page = client.get(reverse("tasks:task-list"), {"page": 2})

    assert len(first_page.context["tasks"]) == 20
    assert first_page.context["page_obj"].number == 1
    assert len(second_page.context["tasks"]) == 1
    assert second_page.context["page_obj"].number == 2


def test_task_detail_displays_relations_and_status(client, author, assignee):
    task = TaskFactory(
        author=author,
        assignee=assignee,
        title="Detailed task",
        is_completed=True,
    )
    client.force_login(author)

    response = client.get(reverse("tasks:task-detail", args=[task.id]))

    assert response.status_code == 200
    assert response.context["task"] == task
    assert task.title in response.content.decode()
    assert author.username in response.content.decode()
    assert assignee.username in response.content.decode()
    assert "Выполнена" in response.content.decode()


def test_author_can_edit_and_unassign_task(client, author, assignee):
    task = TaskFactory(author=author, assignee=assignee, title="Original")
    client.force_login(author)

    response = client.post(
        reverse("tasks:task-update", args=[task.id]),
        {"title": "Updated", "description": "New description", "assignee": ""},
    )

    assert response.status_code == 302
    assert response.url == reverse("tasks:task-detail", args=[task.id])
    task.refresh_from_db()
    assert task.title == "Updated"
    assert task.description == "New description"
    assert task.assignee is None


def test_other_user_cannot_edit_or_delete_task(client, author, other):
    task = TaskFactory(author=author, title="Protected")
    client.force_login(other)
    update_url = reverse("tasks:task-update", args=[task.id])
    delete_url = reverse("tasks:task-delete", args=[task.id])

    assert client.get(update_url).status_code == 403
    assert client.post(update_url, {"title": "Changed"}).status_code == 403
    assert client.get(delete_url).status_code == 403
    assert client.post(delete_url).status_code == 403

    task.refresh_from_db()
    assert task.title == "Protected"
    assert Task.objects.filter(pk=task.pk).exists()


def test_delete_requires_post_and_confirmation(client, author):
    task = TaskFactory(author=author)
    client.force_login(author)
    url = reverse("tasks:task-delete", args=[task.id])

    get_response = client.get(url)
    assert get_response.status_code == 200
    assert "Подтвердите удаление" in get_response.content.decode()
    assert Task.objects.filter(pk=task.pk).exists()

    post_response = client.post(url)
    assert post_response.status_code == 302
    assert post_response.url == reverse("tasks:task-list")
    assert not Task.objects.filter(pk=task.pk).exists()


def test_missing_task_returns_404(client, author):
    client.force_login(author)

    response = client.get(reverse("tasks:task-detail", args=[999999]))

    assert response.status_code == 404

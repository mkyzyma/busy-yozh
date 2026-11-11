import pytest

from tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_user_list_returns_only_public_fields(authenticated_api_client):
    user = UserFactory(email="alice@example.com", is_staff=True)
    client = authenticated_api_client(user)

    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    result = next(item for item in response.data["results"] if item["id"] == user.id)
    assert result == {"id": user.id, "username": user.username}
    assert "password" not in result
    assert "email" not in result
    assert "is_staff" not in result


def test_user_list_excludes_inactive_users(authenticated_api_client):
    active = UserFactory()
    inactive = UserFactory(is_active=False)
    client = authenticated_api_client(active)

    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    user_ids = {item["id"] for item in response.data["results"]}
    assert active.id in user_ids
    assert inactive.id not in user_ids

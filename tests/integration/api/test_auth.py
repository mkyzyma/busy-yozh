import pytest
from rest_framework_simplejwt.tokens import AccessToken

from tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


def test_token_endpoint_returns_access_and_refresh(api_client):
    user = UserFactory()

    response = api_client.post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": DEFAULT_PASSWORD},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["refresh"]


def test_token_endpoint_rejects_invalid_credentials(api_client):
    user = UserFactory()

    response = api_client.post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": "wrong-password"},
        format="json",
    )

    assert response.status_code == 401


def test_refresh_endpoint_returns_new_access(api_client):
    user = UserFactory()
    token_response = api_client.post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": DEFAULT_PASSWORD},
        format="json",
    )

    response = api_client.post(
        "/api/v1/auth/token/refresh/",
        {"refresh": token_response.data["refresh"]},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["access"]


def test_refresh_endpoint_rejects_invalid_token(api_client):
    response = api_client.post(
        "/api/v1/auth/token/refresh/",
        {"refresh": "not-a-valid-refresh-token"},
        format="json",
    )

    assert response.status_code == 401


def test_api_requires_jwt(api_client):
    response = api_client.get("/api/v1/users/")

    assert response.status_code == 401


def test_valid_jwt_allows_api_access(authenticated_api_client):
    user = UserFactory()
    client = authenticated_api_client(user)

    response = client.get("/api/v1/users/")

    assert response.status_code == 200


def test_invalid_jwt_returns_401(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer malformed-token")

    response = api_client.get("/api/v1/users/")

    assert response.status_code == 401


def test_deleted_user_token_cannot_access_api(api_client):
    user = UserFactory()
    token = AccessToken.for_user(user)
    user.delete()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = api_client.get("/api/v1/users/")

    assert response.status_code == 401

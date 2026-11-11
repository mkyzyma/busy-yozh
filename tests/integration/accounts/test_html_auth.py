import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db

PASSWORD = "Strong-pass-123"


def test_signup_creates_user_and_redirects_to_login(client):
    response = client.post(
        "/accounts/signup/",
        {
            "username": "alice",
            "password1": PASSWORD,
            "password2": PASSWORD,
        },
    )

    assert response.status_code == 302
    assert response.url == "/accounts/login/"
    assert get_user_model().objects.filter(username="alice").exists()


def test_signup_rejects_password_mismatch(client):
    response = client.post(
        "/accounts/signup/",
        {
            "username": "alice",
            "password1": PASSWORD,
            "password2": "Different-pass-123",
        },
    )

    assert response.status_code == 200
    assert "password2" in response.context["form"].errors
    assert not get_user_model().objects.filter(username="alice").exists()


def test_login_establishes_session(client):
    user = get_user_model().objects.create_user(username="alice", password=PASSWORD)

    response = client.post(
        "/accounts/login/",
        {"username": user.username, "password": PASSWORD},
    )

    assert response.status_code == 302
    assert response.url == "/tasks/"
    assert client.session["_auth_user_id"] == str(user.pk)


def test_logout_requires_post(client):
    user = get_user_model().objects.create_user(username="alice", password=PASSWORD)
    client.force_login(user)

    response = client.get("/accounts/logout/")

    assert response.status_code == 405
    assert client.session["_auth_user_id"] == str(user.pk)


def test_logout_clears_session(client):
    user = get_user_model().objects.create_user(username="alice", password=PASSWORD)
    client.force_login(user)

    response = client.post("/accounts/logout/")

    assert response.status_code == 302
    assert response.url == "/tasks/"
    assert "_auth_user_id" not in client.session

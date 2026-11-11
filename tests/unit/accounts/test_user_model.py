from django.contrib.auth import get_user_model


def test_user_uses_custom_model():
    assert get_user_model().__name__ == "User"
    assert get_user_model()._meta.app_label == "accounts"

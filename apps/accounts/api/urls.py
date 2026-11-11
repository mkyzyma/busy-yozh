from django.urls import path

from apps.accounts.api.views import UserListAPIView

urlpatterns = [
    path("users/", UserListAPIView.as_view(), name="user-list"),
]

from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.tasks.api.views import (
    CommentListCreateAPIView,
    TaskCompletionAPIView,
    TaskViewSet,
)

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    path(
        "tasks/<int:task_id>/completion/",
        TaskCompletionAPIView.as_view(),
        name="task-completion",
    ),
    path(
        "tasks/<int:task_id>/comments/",
        CommentListCreateAPIView.as_view(),
        name="task-comments",
    ),
    *router.urls,
]

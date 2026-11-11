from typing import cast

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import User
from apps.tasks.api.permissions import CanManageTask
from apps.tasks.api.serializers import TaskListQuerySerializer, TaskSerializer
from apps.tasks.selectors import get_tasks
from apps.tasks.services import delete_task


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, CanManageTask)

    def get_queryset(self):
        query = TaskListQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        filters = {
            f"{key}_id" if key in {"author", "assignee"} else key: value
            for key, value in query.validated_data.items()
        }
        return get_tasks(**filters)

    def perform_create(self, serializer) -> None:
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance) -> None:
        delete_task(task=instance, actor=cast(User, self.request.user))

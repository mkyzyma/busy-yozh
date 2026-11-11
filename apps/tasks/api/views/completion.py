from typing import cast

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tasks.api.permissions.completion import CanChangeTaskCompletion
from apps.tasks.api.serializers import TaskCompletionSerializer, TaskSerializer
from apps.tasks.selectors import get_tasks
from apps.tasks.services import set_task_completion


class TaskCompletionAPIView(APIView):
    permission_classes = (IsAuthenticated, CanChangeTaskCompletion)

    def post(self, request: Request, task_id: int) -> Response:
        task = get_object_or_404(get_tasks(), pk=task_id)
        self.check_object_permissions(request, task)
        serializer = TaskCompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = set_task_completion(
            task=task,
            actor=cast(User, request.user),
            is_completed=serializer.validated_data["is_completed"],
        )
        return Response(TaskSerializer(task, context={"request": request}).data)

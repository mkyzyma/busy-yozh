from django.shortcuts import get_object_or_404
from rest_framework.generics import ListCreateAPIView

from apps.tasks.api.serializers.comment import CommentSerializer
from apps.tasks.models import Task
from apps.tasks.selectors import get_task_comments, get_tasks


class CommentListCreateAPIView(ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_task(self) -> Task:
        return get_object_or_404(get_tasks(), pk=self.kwargs["task_id"])

    def get_queryset(self):
        return get_task_comments(task=self.get_task())

    def perform_create(self, serializer) -> None:
        serializer.save(task=self.get_task(), author=self.request.user)

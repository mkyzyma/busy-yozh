from rest_framework.permissions import BasePermission

from apps.tasks.rules import can_change_task_completion


class CanChangeTaskCompletion(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return can_change_task_completion(user=request.user, task=obj)

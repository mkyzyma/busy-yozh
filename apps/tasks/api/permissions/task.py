from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.tasks.rules import can_edit_task


class CanManageTask(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return can_edit_task(user=request.user, task=obj)

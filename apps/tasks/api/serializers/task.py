from typing import Any

from rest_framework import serializers

from apps.accounts.models import User
from apps.tasks.models import Task
from apps.tasks.services import create_task, update_task


class TaskSerializer(serializers.ModelSerializer):
    """Task data with server-owned fields.

    The author is server-assigned from the authenticated user. Completion is
    read-only here and changes only through the dedicated completion endpoint.
    """

    author: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "author",
            "assignee",
            "is_completed",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "is_completed", "created_at", "updated_at")

    def create(self, validated_data: dict[str, Any]) -> Task:
        return create_task(**validated_data)

    def update(self, instance: Task, validated_data: dict[str, Any]) -> Task:
        for field in ("title", "description", "assignee"):
            if field not in validated_data:
                validated_data[field] = getattr(instance, field)
        return update_task(
            task=instance,
            actor=self.context["request"].user,
            **validated_data,
        )


class TaskListQuerySerializer(serializers.Serializer):
    author = serializers.IntegerField(min_value=1, required=False)
    assignee = serializers.IntegerField(min_value=1, required=False)
    is_completed = serializers.BooleanField(
        required=False,
        allow_null=True,
        default=None,
    )


class TaskCompletionSerializer(serializers.Serializer):
    is_completed = serializers.BooleanField(required=True)
